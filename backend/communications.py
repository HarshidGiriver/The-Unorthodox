"""Durable outbox worker with timezone windows and provider idempotency keys.

External delivery is opt-in. The default transport records a simulation receipt.
Run as a separate process: python -m backend.communications --once (or --watch).
"""

import argparse
from datetime import datetime, time as wall_time, timezone
import json
import logging
import os
import time
import uuid
from zoneinfo import ZoneInfo

import requests

from backend.config import (
    BANK_NAME, BANK_GRIEVANCE_OFFICER_NAME, BANK_GRIEVANCE_OFFICER_EMAIL,
    BANK_GRIEVANCE_OFFICER_PHONE, RBI_CALL_HOURS_START, RBI_CALL_HOURS_END,
)
from backend.storage import Database
from backend.workflow import event

logger = logging.getLogger(__name__)


def contact_window(current=None):
    current = current or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Contact time must have an explicit timezone")
    local = current.astimezone(ZoneInfo(os.getenv("CONTACT_TIMEZONE", "Asia/Kolkata"))).time()
    start, end = wall_time.fromisoformat(RBI_CALL_HOURS_START), wall_time.fromisoformat(RBI_CALL_HOURS_END)
    if start >= end:
        raise ValueError("Contact window must start before it ends")
    return start <= local < end


def build_notice(proposal_id, version, plan, borrower, channel):
    """Financial terms and disclosures are always deterministic; no LLM edits."""
    body = (
        f"{BANK_NAME}: Proposal {proposal_id}, version {version}, for account {borrower['customer_id']}. "
        f"Voluntary proposal; acceptance is required. Current payment INR {plan['old_emi']:.2f}; "
        f"proposed regular payment INR {plan['new_emi']:.2f}; term {plan['new_tenure_months']} months; "
        f"APR {plan['new_annual_rate'] * 100:.2f}%. "
        f"Interest-only period {plan['moratorium_months']} months at INR {plan['moratorium_payment']:.2f}/month. "
        f"Total interest INR {plan['total_interest_new']:.2f}, original INR {plan['total_interest_old']:.2f}. "
        "The final installment may differ by rounding; review the full schedule in your authenticated portal. "
        f"Questions: {BANK_GRIEVANCE_OFFICER_NAME}, {BANK_GRIEVANCE_OFFICER_EMAIL}, {BANK_GRIEVANCE_OFFICER_PHONE}."
    )
    return {"channel": channel, "recipient": borrower["email" if channel == "email" else "phone"],
            "contact_verified": bool(borrower["contact_verified"]), "simulation": bool(borrower["simulation"]),
            "subject": f"Kintsugi voluntary proposal v{version}", "body": body}


class DeliveryTransport:
    def send(self, payload, idempotency_key):
        mode = os.getenv("DELIVERY_MODE", "simulate")
        if mode == "simulate" or payload["simulation"]:
            return "simulated", f"simulation:{idempotency_key}"
        if mode != "webhook":
            raise ValueError("DELIVERY_MODE must be simulate or webhook")
        if not payload["contact_verified"] or not payload["recipient"]:
            raise ValueError("Verified recipient required for external delivery")
        endpoint = os.getenv("DELIVERY_WEBHOOK_URL", "")
        secret = os.getenv("DELIVERY_WEBHOOK_TOKEN", "")
        if not endpoint.startswith("https://") or not secret:
            raise ValueError("Configure an HTTPS delivery gateway and token")
        # The configured gateway MUST persist this key and return the original receipt on retries.
        response = requests.post(
            endpoint, json={k: payload[k] for k in ("channel", "recipient", "subject", "body")},
            headers={"Authorization": f"Bearer {secret}", "Idempotency-Key": idempotency_key},
            timeout=(3, 15), allow_redirects=False,
        )
        response.raise_for_status()
        receipt = response.json().get("receipt_id")
        if not isinstance(receipt, str) or not receipt:
            raise ValueError("Gateway must return a nonempty receipt_id")
        return "sent", receipt


def process_one(database, transport=None, current=None):
    current = current or datetime.now(timezone.utc)
    if not contact_window(current):
        return False
    timestamp = current.timestamp()
    claim = str(uuid.uuid4())
    with database.transaction() as connection:
        # Recover a crashed worker after its lease. Stable outbox IDs prevent provider duplicates.
        connection.execute(
            "UPDATE outbox SET status=CASE WHEN attempts>=5 THEN 'failed' ELSE 'queued' END,claim_token=NULL WHERE status='sending' AND claimed_at<?",
            (timestamp - 300,),
        )
        row = connection.execute(
            "SELECT * FROM outbox WHERE status IN ('queued','retry') AND available_at<=? AND attempts<5 ORDER BY rowid LIMIT 1",
            (timestamp,),
        ).fetchone()
        if row is None:
            return False
        connection.execute("UPDATE outbox SET status='sending',attempts=attempts+1,claimed_at=?,claim_token=? WHERE id=?",
                           (timestamp, claim, row["id"]))
    try:
        status, receipt = (transport or DeliveryTransport()).send(json.loads(row["payload"]), row["id"])
        with database.transaction() as connection:
            changed = connection.execute(
                "UPDATE outbox SET status=?,receipt=?,last_error=NULL WHERE id=? AND claim_token=?",
                (status, receipt, row["id"], claim),
            ).rowcount
            if changed:
                event(connection, "delivery-worker", f"notification_{status}", row["proposal_id"], row["channel"])
        logger.info("delivery_result", extra={"outbox_id": row["id"], "delivery_status": status})
    except Exception as exc:
        attempts = row["attempts"] + 1
        with database.transaction() as connection:
            connection.execute(
                "UPDATE outbox SET status=?,available_at=?,last_error=? WHERE id=? AND claim_token=?",
                ("failed" if attempts >= 5 else "retry", timestamp + min(3600, 60 * 2 ** attempts),
                 type(exc).__name__, row["id"], claim),
            )
        logger.warning("delivery_retry", extra={"outbox_id": row["id"], "error_type": type(exc).__name__})
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    from backend.observability import configure_logging
    configure_logging()
    database = Database()
    while True:
        process_one(database)
        if not args.watch:
            break
        time.sleep(5)


if __name__ == "__main__":
    main()
