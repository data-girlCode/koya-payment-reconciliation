#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

latest = {}

total = 0.0
count = 0

with open("payments.jsonl", "r", encoding="utf-8", errors="replace") as f:
    for line_number, line in enumerate(f):
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if txn_id is None or txn_id == "":
            continue

        try:
            timestamp = datetime.fromisoformat(
                event["ts"].replace("Z", "+00:00")
            )

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

        except (KeyError, ValueError, TypeError):
            continue

        previous = latest.get(txn_id)

        # Keep only the latest attempt.
        # If timestamps tie, the later line wins.
        if previous is None or (timestamp, line_number) > previous[:2]:
            latest[txn_id] = (timestamp, line_number, event)


total = Decimal("0")
count = 0

for _, _, event in latest.values():
    if event["status"] == "success":
        amount = str(event["amount"]).strip()
        amount = amount.replace("₦", "").replace(",", "").replace("NGN", "").strip()
        total += Decimal(amount)
        count += 1


expected = int(Path("expected.txt").read_text().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
