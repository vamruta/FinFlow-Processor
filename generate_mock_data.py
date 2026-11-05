#!/usr/bin/env python
# generate_mock_data.py
# ------------------------------------------------------------
# This script creates a CSV file named ``raw_transactions.csv``
# containing 500 rows of synthetic financial transaction data.
# Five rows are intentionally malformed to help test the
# ``ErrorLog`` handling logic of the FinFlow Processor service.
# ------------------------------------------------------------

import csv
import random
import uuid
from datetime import datetime, timedelta

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
TOTAL_ROWS = 500
DIRTY_ROWS = 5
OUTPUT_FILE = "raw_transactions.csv"

# Simple static list of merchants and currencies – feel free to expand.
MERCHANTS = [
    "Amazon",
    "Walmart",
    "Target",
    "Starbucks",
    "Apple",
    "Google",
    "Netflix",
    "Uber",
    "Airbnb",
    "Stripe",
]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD"]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def random_timestamp(start: datetime, end: datetime) -> str:
    """Return a random timestamp between *start* and *end* as ISO string."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=random_seconds)).isoformat()


def random_transaction_id(existing_ids: set) -> str:
    """Generate a unique transaction_id.

    The format mimics the example ``TXN100234``. If a duplicate is needed
    (for a dirty row) callers can supply an existing id.
    """
    while True:
        tid = f"TXN{random.randint(100000, 999999)}"
        if tid not in existing_ids:
            existing_ids.add(tid)
            return tid


def random_account_number() -> str:
    return f"ACC{random.randint(100000, 999999)}"


def random_amount() -> float:
    # Positive amounts between 1.00 and 5000.00
    return round(random.uniform(1.0, 5000.0), 2)


def random_currency() -> str:
    return random.choice(CURRENCIES)


def random_merchant() -> str:
    return random.choice(MERCHANTS)

# ------------------------------------------------------------
# Main generation logic
# ------------------------------------------------------------
def generate_data():
    start_date = datetime.now() - timedelta(days=365)  # one year back
    end_date = datetime.now()

    rows = []
    used_ids = set()

    # 1. Generate clean rows
    for _ in range(TOTAL_ROWS - DIRTY_ROWS):
        rows.append({
            "transaction_id": random_transaction_id(used_ids),
            "account_number": random_account_number(),
            "amount": f"{random_amount():.2f}",
            "currency": random_currency(),
            "merchant": random_merchant(),
            "timestamp": random_timestamp(start_date, end_date),
        })

    # 2. Introduce dirty rows (randomly intermix them later)
    dirty_examples = []

    # a) Missing amount
    dirty_examples.append({
        "transaction_id": random_transaction_id(used_ids),
        "account_number": random_account_number(),
        "amount": "",  # empty field
        "currency": random_currency(),
        "merchant": random_merchant(),
        "timestamp": random_timestamp(start_date, end_date),
    })

    # b) Negative amount
    dirty_examples.append({
        "transaction_id": random_transaction_id(used_ids),
        "account_number": random_account_number(),
        "amount": f"{-random_amount():.2f}",
        "currency": random_currency(),
        "merchant": random_merchant(),
        "timestamp": random_timestamp(start_date, end_date),
    })

    # c) Duplicate transaction_id (use an existing one)
    duplicate_id = random.choice(list(used_ids))
    dirty_examples.append({
        "transaction_id": duplicate_id,
        "account_number": random_account_number(),
        "amount": f"{random_amount():.2f}",
        "currency": random_currency(),
        "merchant": random_merchant(),
        "timestamp": random_timestamp(start_date, end_date),
    })

    # d) Missing merchant name
    dirty_examples.append({
        "transaction_id": random_transaction_id(used_ids),
        "account_number": random_account_number(),
        "amount": f"{random_amount():.2f}",
        "currency": random_currency(),
        "merchant": "",  # empty merchant
        "timestamp": random_timestamp(start_date, end_date),
    })

    # e) Completely malformed (e.g., missing several columns)
    dirty_examples.append({
        "transaction_id": "",  # missing id
        "account_number": "",
        "amount": "",
        "currency": "",
        "merchant": "",
        "timestamp": "",
    })

    rows.extend(dirty_examples)

    # Shuffle to avoid all dirty rows being at the end
    random.shuffle(rows)

    # 3. Write CSV
    fieldnames = ["transaction_id", "account_number", "amount", "currency", "merchant", "timestamp"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Generated {len(rows)} rows (including {DIRTY_ROWS} dirty rows) to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    generate_data()
