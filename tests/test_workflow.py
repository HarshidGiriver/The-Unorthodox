"""Persistence, authorization, immutable consent, delivery and concurrency tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import pytest

from backend.auth import hash_password, login, logout
from backend.communications import contact_window, process_one
from backend.data.loader import load_customer_data
from backend.storage import Database
from backend.workflow import Workflow, import_portfolio


@pytest.fixture
def system(tmp_path):
    database = Database(tmp_path / "test.sqlite3")
    frame = load_customer_data().head(2).copy()
    frame["monthly_income"] = 100000
    import_portfolio(database, frame)
    ids = frame.customer_id.tolist()
    hashed = hash_password("A test password 123!")
    with database.transaction() as connection:
        for username, role, customer in [("officer", "underwriter", None), ("borrower", "borrower", ids[0]),
                                         ("other", "borrower", ids[1])]:
            connection.execute("INSERT INTO users(username,password_hash,role,customer_id) VALUES (?,?,?,?)",
                               (username, hashed, role, customer))
    tokens = {name: login(database, name, "A test password 123!") for name in ("officer", "borrower", "other")}
    return database, Workflow(database), ids, tokens


def approved(system):
    database, workflow, ids, tokens = system
    proposal = workflow.create_proposal(tokens["officer"], ids[0], tenure_extension_months=12)
    workflow.decide(tokens["officer"], proposal, True, "Reviewed disposable income and full schedule")
    return proposal


def test_complete_workflow_persists_and_activation_is_idempotent(system):
    database, workflow, ids, tokens = system
    proposal = approved(system)
    saved = workflow.proposals(tokens["borrower"])[0]
    workflow.consent(tokens["borrower"], proposal, saved["terms_hash"])
    workflow.activate(tokens["borrower"], proposal)
    workflow.activate(tokens["officer"], proposal)
    fresh = Workflow(Database(database.path))
    assert fresh.proposals(tokens["borrower"])[0]["status"] == "active"
    with database.connect() as connection:
        loan = connection.execute("SELECT * FROM loans WHERE customer_id=?", (ids[0],)).fetchone()
        assert loan["version"] == 2
        assert json.loads(loan["schedule"])[-1]["ending_balance"] == 0
    assert sum(e["action"] == "activated_locally" for e in fresh.activity(tokens["officer"])["events"]) == 1


def test_role_and_customer_permissions(system):
    _, workflow, ids, tokens = system
    proposal = approved(system)
    with pytest.raises(PermissionError):
        workflow.create_proposal(tokens["borrower"], ids[0])
    with pytest.raises(PermissionError):
        workflow.decide(tokens["borrower"], proposal, True, "no")
    with pytest.raises(PermissionError):
        workflow.consent(tokens["other"], proposal, "wrong")
    with pytest.raises(PermissionError):
        workflow.activate(tokens["other"], proposal)
    assert workflow.proposals(tokens["other"]) == []
    assert workflow.portfolio(tokens["borrower"]).customer_id.tolist() == [ids[0]]


def test_exact_consent_and_stale_loan_cannot_activate(system):
    _, workflow, ids, tokens = system
    first = approved(system)
    second = approved(system)
    with pytest.raises(ValueError):
        workflow.activate(tokens["officer"], first)
    with pytest.raises(ValueError):
        workflow.consent(tokens["borrower"], first, "tampered")
    for proposal in workflow.proposals(tokens["borrower"]):
        workflow.consent(tokens["borrower"], proposal["id"], proposal["terms_hash"])
    workflow.activate(tokens["borrower"], first)
    with pytest.raises(ValueError):
        workflow.activate(tokens["borrower"], second)


def test_affordability_blocks_approval(system):
    database, workflow, ids, tokens = system
    with database.transaction() as connection:
        row = connection.execute("SELECT payload FROM borrowers WHERE customer_id=?", (ids[0],)).fetchone()
        profile = json.loads(row[0]); profile["monthly_income"] = 1
        connection.execute("UPDATE borrowers SET payload=? WHERE customer_id=?", (json.dumps(profile), ids[0]))
    proposal = workflow.create_proposal(tokens["officer"], ids[0])
    with pytest.raises(ValueError, match="available income"):
        workflow.decide(tokens["officer"], proposal, True, "reviewed")


def test_delivery_window_retry_and_simulation(system, monkeypatch):
    database, workflow, _, tokens = system
    approved(system)
    monkeypatch.setenv("CONTACT_TIMEZONE", "Asia/Kolkata")
    inside = datetime(2026, 9, 24, 5, tzinfo=timezone.utc)
    outside = datetime(2026, 9, 24, 20, tzinfo=timezone.utc)
    assert contact_window(inside) and not contact_window(outside)
    assert not process_one(database, current=outside)

    class FailingTransport:
        def send(self, payload, idempotency_key):
            raise TimeoutError("provider unavailable")

    process_one(database, FailingTransport(), inside)
    with database.connect() as connection:
        failed = connection.execute("SELECT * FROM outbox WHERE status='retry'").fetchone()
        original_id = failed["id"]
    with database.transaction() as connection:
        connection.execute("UPDATE outbox SET available_at=0")
    seen = []

    class SuccessfulTransport:
        def send(self, payload, idempotency_key):
            seen.append(idempotency_key)
            return "simulated", "test-receipt"

    process_one(database, SuccessfulTransport(), inside)
    assert seen == [original_id]
    assert workflow.activity(tokens["officer"])["delivery"]


def test_concurrent_workers_claim_each_message_once(system):
    database, _, _, _ = system
    approved(system)
    seen = []

    class Transport:
        def send(self, payload, key):
            seen.append(key)
            return "simulated", key

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: process_one(database, Transport(), datetime(2026, 9, 24, 5, tzinfo=timezone.utc)), range(4)))
    assert len(seen) == len(set(seen)) == 2


def test_logout_revokes_session_and_receipts_are_unique(system):
    database, workflow, ids, tokens = system
    workflow.record_payment(tokens["officer"], ids[0], 100, "payment-1")
    assert workflow.repayment_summary(tokens["borrower"], ids[0])["recorded_receipts"] == 100
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        workflow.record_payment(tokens["officer"], ids[0], 100, "payment-1")
    logout(database, tokens["borrower"])
    with pytest.raises(PermissionError):
        workflow.principal(tokens["borrower"])


def test_saved_workflow_ui_renders_review_and_exact_consent(system, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    database, workflow, ids, tokens = system
    monkeypatch.setenv("KINTSUGI_DB_PATH", str(database.path))
    workflow.create_proposal(tokens["officer"], ids[0])
    app = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "app.py"), default_timeout=40)
    app.session_state["app_mode"] = "Saved workflow"
    app.session_state["auth_token"] = tokens["officer"]
    app.run()
    assert not app.exception
    next(x for x in app.text_area if x.label.startswith("Review rationale")).set_value("Affordability and schedule reviewed")
    next(x for x in app.checkbox if x.label.startswith("I reviewed affordability")).check()
    next(x for x in app.button if x.label == "Record decision").click().run()
    assert not app.exception
    assert workflow.proposals(tokens["officer"])[0]["status"] == "approved"
    borrower = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "app.py"), default_timeout=40)
    borrower.session_state["app_mode"] = "Saved workflow"
    borrower.session_state["auth_token"] = tokens["borrower"]
    borrower.run()
    assert not borrower.exception
    next(x for x in borrower.checkbox if x.label.startswith("I reviewed these exact")).check().run()
    next(x for x in borrower.button if x.label == "Record my consent").click().run()
    next(x for x in borrower.button if x.label == "Activate accepted plan in local ledger").click().run()
    assert not borrower.exception
    assert workflow.proposals(tokens["borrower"])[0]["status"] == "active"


def test_contact_window_boundaries_and_gateway_contract(monkeypatch):
    from backend.communications import DeliveryTransport
    monkeypatch.setenv("CONTACT_TIMEZONE", "Asia/Kolkata")
    assert contact_window(datetime(2026, 9, 24, 2, 30, tzinfo=timezone.utc))
    assert not contact_window(datetime(2026, 9, 24, 13, 30, tzinfo=timezone.utc))
    monkeypatch.setenv("DELIVERY_MODE", "webhook")
    monkeypatch.setenv("DELIVERY_WEBHOOK_URL", "https://gateway.example/messages")
    monkeypatch.setenv("DELIVERY_WEBHOOK_TOKEN", "test-only-token")
    payload = {"channel": "email", "recipient": "test@example.invalid", "subject": "Review",
               "body": "Deterministic terms", "contact_verified": True, "simulation": False}
    captured = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"receipt_id": "receipt-1"}

    def post(url, **kwargs):
        captured.append((url, kwargs))
        return Response()

    monkeypatch.setattr("backend.communications.requests.post", post)
    assert DeliveryTransport().send(payload, "stable-id") == ("sent", "receipt-1")
    assert captured[0][1]["headers"]["Idempotency-Key"] == "stable-id"
    payload["simulation"] = True
    assert DeliveryTransport().send(payload, "another-id")[0] == "simulated"
    assert len(captured) == 1  # Even webhook mode cannot send generated demo accounts.


def test_failed_login_lock_and_expired_session(system):
    import time
    database, workflow, _, tokens = system
    for _ in range(5):
        with pytest.raises(PermissionError):
            login(database, "officer", "incorrect-password")
    with pytest.raises(PermissionError):
        login(database, "officer", "A test password 123!")
    with database.transaction() as connection:
        connection.execute("UPDATE sessions SET expires_at=?", (time.time() - 1,))
    with pytest.raises(PermissionError):
        workflow.principal(tokens["officer"])


def test_approval_is_atomic_and_does_not_duplicate_outbox(system):
    database, workflow, _, tokens = system
    proposal = approved(system)
    with pytest.raises(ValueError):
        workflow.decide(tokens["officer"], proposal, True, "repeat")
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
