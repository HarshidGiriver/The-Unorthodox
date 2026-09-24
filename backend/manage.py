"""Local operator commands. Run on the trusted server, never expose as an HTTP endpoint."""

import argparse
import getpass
import json

from backend.auth import hash_password
from backend.storage import Database
from backend.workflow import import_portfolio, event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-demo")
    importer = commands.add_parser("import-csv")
    importer.add_argument("path")
    user = commands.add_parser("create-user")
    user.add_argument("username")
    user.add_argument("--role", choices=["underwriter", "borrower"], required=True)
    user.add_argument("--customer-id")
    contact = commands.add_parser("verify-contact")
    contact.add_argument("customer_id")
    contact.add_argument("--email")
    contact.add_argument("--phone")
    commands.add_parser("health")
    args = parser.parse_args()
    database = Database()
    if args.command in ("init-demo", "import-csv"):
        from backend.data.loader import load_customer_data
        import_portfolio(database, load_customer_data(args.path if args.command == "import-csv" else None))
        print("Portfolio imported; existing accounts preserved.")
    elif args.command == "create-user":
        if (args.role == "borrower") != bool(args.customer_id):
            parser.error("Only borrower users require --customer-id")
        password = getpass.getpass("Password (at least 12 characters): ")
        if password != getpass.getpass("Repeat password: "):
            parser.error("Passwords differ")
        with database.transaction() as connection:
            connection.execute("INSERT INTO users(username,password_hash,role,customer_id) VALUES (?,?,?,?)",
                               (args.username, hash_password(password), args.role, args.customer_id))
            event(connection, "local-operator", "user_created", detail=args.username)
        print("User created.")
    elif args.command == "verify-contact":
        if not args.email and not args.phone:
            parser.error("Provide a verified email or phone number")
        with database.transaction() as connection:
            changed = connection.execute(
                "UPDATE borrowers SET email=?,phone=?,contact_verified=1 WHERE customer_id=?",
                (args.email, args.phone, args.customer_id),
            ).rowcount
            if not changed:
                parser.error("Unknown borrower")
            event(connection, "local-operator", "contact_verified", detail=args.customer_id)
        print("Operator-verified contact saved. Generated demo contacts cannot receive external messages.")
    else:
        with database.connect() as connection:
            check = connection.execute("PRAGMA integrity_check").fetchone()[0]
            queue = dict(connection.execute("SELECT status,COUNT(*) FROM outbox GROUP BY status").fetchall())
        from backend.agents.detection_agent import StressDetectionAgent
        agent = StressDetectionAgent()
        print(json.dumps({"database": check, "scoring_mode": "model" if agent.model is not None else "heuristic",
                          "outbox": queue}))
        if check != "ok":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
