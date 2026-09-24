"""Password hashing and expiring opaque sessions for local deployments."""

import hashlib
import hmac
import secrets
import time


def hash_password(password):
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Use a password of at least 12 characters")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password, encoded):
    _, rounds, salt, expected = encoded.split("$")
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
    return hmac.compare_digest(actual, expected)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def identity(connection, token, role=None, customer_id=None):
    if not isinstance(token, str) or not token:
        raise PermissionError("Sign in again: session missing or expired")
    row = connection.execute(
        "SELECT u.username,u.role,u.customer_id FROM sessions s JOIN users u ON u.username=s.username "
        "WHERE s.token_hash=? AND s.expires_at>?", (token_hash(token), time.time())
    ).fetchone()
    if row is None:
        raise PermissionError("Sign in again: session missing or expired")
    if role and row["role"] != role:
        raise PermissionError(f"This action requires the {role} role")
    if row["role"] == "borrower" and customer_id and row["customer_id"] != customer_id:
        raise PermissionError("This account belongs to another borrower")
    return dict(row)


def login(database, username, password):
    now = time.time()
    token = None
    with database.transaction() as connection:
        user = connection.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and user["locked_until"] <= now and verify_password(password, user["password_hash"]):
            token = secrets.token_urlsafe(32)
            connection.execute("INSERT INTO sessions VALUES (?,?,?)", (token_hash(token), username, now + 3600))
            connection.execute("UPDATE users SET failed_attempts=0,locked_until=0 WHERE username=?", (username,))
        elif user and user["locked_until"] <= now:
            failures = user["failed_attempts"] + 1
            connection.execute("UPDATE users SET failed_attempts=?,locked_until=? WHERE username=?",
                               (failures, now + 300 if failures >= 5 else 0, username))
    if token is None:
        raise PermissionError("Invalid credentials or temporarily locked account")
    return token


def logout(database, token):
    with database.transaction() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(token),))
