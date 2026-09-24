"""Authorized, transactional proposal lifecycle. Terms are immutable once saved."""

from datetime import datetime, timezone
import hashlib
import json
import uuid

from backend.auth import identity
from backend.agents.restructuring_agent import DebtRestructuringAgent
from backend.data.loader import normalize_customers, REQUIRED_COLUMNS
from backend.finance import number


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def event(connection, actor, action, proposal_id=None, detail=""):
    connection.execute(
        "INSERT INTO audit_events(proposal_id,actor,action,detail,created_at) VALUES (?,?,?,?,?)",
        (proposal_id, actor, action, detail, now()),
    )


def import_portfolio(database, portfolio):
    """Local operator import. Existing loan state is deliberately never overwritten."""
    frame = normalize_customers(portfolio)
    solver = DebtRestructuringAgent()
    with database.transaction() as connection:
        for row in frame.to_dict("records"):
            row = {key: row[key] for key in REQUIRED_COLUMNS}
            customer_id = row["customer_id"]
            if connection.execute("SELECT 1 FROM borrowers WHERE customer_id=?", (customer_id,)).fetchone():
                continue
            connection.execute("INSERT INTO borrowers(customer_id,payload,simulation) VALUES (?,?,?)",
                               (customer_id, encode(row), int(frame.attrs.get("simulation", False))))
            schedule = solver.generate_amortization_schedule(
                row["remaining_principal"], row["annual_interest_rate"], row["remaining_tenure_months"]
            ).to_dict("records")
            connection.execute(
                "INSERT INTO loans(customer_id,principal,emi,tenure,rate,schedule,updated_at) VALUES (?,?,?,?,?,?,?)",
                (customer_id, row["remaining_principal"], row["current_emi"], row["remaining_tenure_months"],
                 row["annual_interest_rate"], encode(schedule), now()),
            )
        event(connection, "local-operator", "portfolio_import")


class Workflow:
    def __init__(self, database):
        self.database = database

    def principal(self, token):
        with self.database.connect() as connection:
            return identity(connection, token)

    def portfolio(self, token):
        import pandas as pd
        from backend.agents.detection_agent import StressDetectionAgent
        with self.database.connect() as connection:
            actor = identity(connection, token)
            query = "SELECT b.*,l.* FROM borrowers b JOIN loans l USING(customer_id)"
            args = ()
            if actor["role"] == "borrower":
                query += " WHERE b.customer_id=?"
                args = (actor["customer_id"],)
            rows = connection.execute(query, args).fetchall()
        records = []
        for row in rows:
            item = json.loads(row["payload"])
            item.update(remaining_principal=row["principal"], current_emi=row["emi"],
                        remaining_tenure_months=row["tenure"], annual_interest_rate=row["rate"])
            records.append(item)
        if not records:
            return pd.DataFrame()
        frame = pd.DataFrame(records)
        frame.attrs["simulation"] = any(row["simulation"] for row in rows)
        if frame.attrs["simulation"]:
            frame.attrs["data_warning"] = "Includes simulated borrower finances. Stored workflow actions affect this local database only."
        return StressDetectionAgent().analyze_portfolio(frame)

    def create_proposal(self, token, customer_id, **parameters):
        with self.database.transaction() as connection:
            actor = identity(connection, token, "underwriter")
            loan = connection.execute("SELECT * FROM loans WHERE customer_id=?", (customer_id,)).fetchone()
            borrower = connection.execute("SELECT * FROM borrowers WHERE customer_id=?", (customer_id,)).fetchone()
            if loan is None:
                raise ValueError("Borrower loan not found")
            if connection.execute("SELECT 1 FROM payments WHERE customer_id=?", (customer_id,)).fetchone():
                raise ValueError("Payments exist: reconcile the outstanding balance before creating another proposal")
            if loan["version"] > 1:
                raise ValueError("An active restructured schedule already exists; servicing review is required before another restructure")
            profile = json.loads(borrower["payload"])
            plan = DebtRestructuringAgent().optimize_restructuring(
                loan["principal"], loan["emi"], loan["tenure"], loan["rate"], **parameters
            )
            for key in ("amortization_schedule", "original_schedule"):
                plan[key] = plan[key].to_dict("records")
            disposable = max(0, profile["monthly_income"] - profile["monthly_expenses"])
            maximum_payment = max(item["emi"] for item in plan["amortization_schedule"])
            plan.update(available_income=round(disposable, 2), affordable=maximum_payment <= disposable,
                        simulation=bool(borrower["simulation"]))
            from backend.agents.detection_agent import StressDetectionAgent
            import pandas as pd
            scored = StressDetectionAgent().analyze_portfolio(pd.DataFrame([profile]))
            score_context = {"score": float(scored.iloc[0]["anomaly_score"]),
                             "tier": scored.iloc[0]["risk_tier"], **scored.attrs}
            version = connection.execute(
                "SELECT COALESCE(MAX(version),0)+1 FROM proposals WHERE customer_id=?", (customer_id,)
            ).fetchone()[0]
            proposal_id = str(uuid.uuid4())
            terms = encode(plan)
            connection.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?,?)",
                               (proposal_id, customer_id, version, loan["version"], "draft", terms,
                                hashlib.sha256(terms.encode()).hexdigest(), encode(score_context), actor["username"], now()))
            event(connection, actor["username"], "proposal_created", proposal_id)
            return proposal_id

    @staticmethod
    def _proposal(connection, proposal_id):
        row = connection.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if row is None:
            raise ValueError("Proposal not found")
        return row

    def proposals(self, token):
        with self.database.connect() as connection:
            actor = identity(connection, token)
            query = "SELECT * FROM proposals"
            args = ()
            if actor["role"] == "borrower":
                query += " WHERE customer_id=? AND status IN ('approved','consented','active')"
                args = (actor["customer_id"],)
            rows = connection.execute(query + " ORDER BY created_at DESC", args).fetchall()
            return [dict(row, terms=json.loads(row["terms"])) for row in rows]

    def decide(self, token, proposal_id, approve, reason):
        if not isinstance(approve, bool) or not reason.strip():
            raise ValueError("A review decision and reason are required")
        with self.database.transaction() as connection:
            actor = identity(connection, token, "underwriter")
            proposal = self._proposal(connection, proposal_id)
            if proposal["status"] != "draft":
                raise ValueError("Only draft proposals can be reviewed")
            plan = json.loads(proposal["terms"])
            if approve and not plan["affordable"]:
                raise ValueError("Proposed payments exceed available income; revise the terms before approval")
            state = "approved" if approve else "rejected"
            connection.execute("UPDATE proposals SET status=? WHERE id=?", (state, proposal_id))
            connection.execute("INSERT INTO decisions VALUES (?,?,?,?,?)",
                               (proposal_id, actor["username"], state, reason.strip(), now()))
            if approve:
                from backend.communications import build_notice
                borrower = connection.execute("SELECT * FROM borrowers WHERE customer_id=?",
                                              (proposal["customer_id"],)).fetchone()
                for channel in ("email", "sms"):
                    notice = build_notice(proposal_id, proposal["version"], plan, dict(borrower), channel)
                    connection.execute("INSERT INTO outbox(id,proposal_id,channel,payload) VALUES (?,?,?,?)",
                                       (str(uuid.uuid4()), proposal_id, channel, encode(notice)))
            event(connection, actor["username"], state, proposal_id, reason.strip())

    def consent(self, token, proposal_id, terms_hash):
        with self.database.transaction() as connection:
            proposal = self._proposal(connection, proposal_id)
            actor = identity(connection, token, "borrower", proposal["customer_id"])
            if proposal["status"] != "approved" or terms_hash != proposal["terms_hash"]:
                raise ValueError("Review the current approved proposal before consenting")
            connection.execute("INSERT INTO consents VALUES (?,?,?,?)",
                               (proposal_id, actor["username"], terms_hash, now()))
            connection.execute("UPDATE proposals SET status='consented' WHERE id=?", (proposal_id,))
            event(connection, actor["username"], "consented", proposal_id, terms_hash)

    def activate(self, token, proposal_id):
        with self.database.transaction() as connection:
            proposal = self._proposal(connection, proposal_id)
            actor = identity(connection, token, customer_id=proposal["customer_id"])
            if proposal["status"] == "active":
                return  # Idempotent activation never duplicates a ledger update.
            if proposal["status"] != "consented":
                raise ValueError("Approval and borrower consent are required before activation")
            consent = connection.execute("SELECT * FROM consents WHERE proposal_id=?", (proposal_id,)).fetchone()
            if consent is None or consent["terms_hash"] != proposal["terms_hash"]:
                raise ValueError("Consent does not match the immutable proposal terms")
            plan = json.loads(proposal["terms"])
            changed = connection.execute(
                "UPDATE loans SET version=version+1,emi=?,tenure=?,rate=?,schedule=?,updated_at=? "
                "WHERE customer_id=? AND version=?",
                (plan["new_emi"], plan["new_tenure_months"], plan["new_annual_rate"],
                 encode(plan["amortization_schedule"]), now(), proposal["customer_id"], proposal["loan_version"]),
            ).rowcount
            if changed != 1:
                raise ValueError("Loan changed since this proposal was created; request a new review")
            connection.execute("UPDATE proposals SET status='active' WHERE id=?", (proposal_id,))
            event(connection, actor["username"], "activated_locally", proposal_id)

    def activity(self, token):
        with self.database.connect() as connection:
            identity(connection, token, "underwriter")
            events = [dict(r) for r in connection.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 100")]
            delivery = [dict(r) for r in connection.execute(
                "SELECT id,proposal_id,channel,status,attempts,receipt,last_error FROM outbox ORDER BY rowid DESC LIMIT 100"
            )]
            return {"events": events, "delivery": delivery}

    def record_payment(self, token, customer_id, amount, reference):
        number(amount, "amount", 0.01)
        if not reference.strip():
            raise ValueError("A unique payment reference is required")
        with self.database.transaction() as connection:
            actor = identity(connection, token, "underwriter")
            loan = connection.execute("SELECT * FROM loans WHERE customer_id=?", (customer_id,)).fetchone()
            if loan is None:
                raise ValueError("Loan not found")
            connection.execute("INSERT INTO payments VALUES (?,?,?,?,?,?)",
                               (reference.strip(), customer_id, loan["version"], round(amount, 2), actor["username"], now()))
            event(connection, actor["username"], "payment_recorded", detail=reference.strip())

    def repayment_summary(self, token, customer_id):
        with self.database.connect() as connection:
            identity(connection, token, customer_id=customer_id)
            loan = connection.execute("SELECT * FROM loans WHERE customer_id=?", (customer_id,)).fetchone()
            if loan is None:
                raise ValueError("Loan not found")
            total = connection.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE customer_id=? AND loan_version=?",
                                       (customer_id, loan["version"])).fetchone()[0]
            scheduled = sum(row["emi"] for row in json.loads(loan["schedule"]))
            return {"recorded_receipts": total, "scheduled_total": round(scheduled, 2),
                    "uncollected_scheduled_total": round(max(0, scheduled - total), 2),
                    "note": "Receipt tracking only; not a reconciled principal balance or delinquency calculation."}
