# ------------------------------------------------------------
# ETL Pipeline Script for FinFlow Processor
# ------------------------------------------------------------
# Extract: Reads raw_transactions.csv using Pandas.
# Transform & Validate:
#   - Amount must be greater than 0.
#   - Mandatory fields (transaction_id, account_number, timestamp, merchant)
#     must not be empty or null.
#   - transaction_id must not be duplicated within the batch or in PostgreSQL.
# Load:
#   - Insert valid rows into the 'transactions' table in PostgreSQL.
#   - Insert invalid rows with error reasons into the 'error_logs' table.
# Summary: Logs total processed, total successful, total failed.
# ------------------------------------------------------------

import json
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

# Ensure UTF-8 output encoding for console safety
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.database import Base, SessionLocal, engine
from app.models.transaction import ErrorLog, Transaction

CSV_FILE = "raw_transactions.csv"


def is_empty_or_null(val) -> bool:
    """Helper to detect if a value is None, NaN, or empty string."""
    if val is None or pd.isna(val):
        return True
    s = str(val).strip()
    return s == "" or s.lower() == "nan"


def validate_transaction_row(
    row: dict,
    seen_batch_ids: set = None,
    existing_db_ids: set = None,
) -> tuple:
    """
    Validate a single transaction dictionary against business and data rules.
    Returns:
        tuple: (is_valid: bool, error_reason: str or None, amount: float or None, timestamp: datetime or None)
    """
    raw_tx_id = row.get("transaction_id")
    raw_acc_num = row.get("account_number")
    raw_amount = row.get("amount")
    raw_merchant = row.get("merchant")
    raw_timestamp = row.get("timestamp")

    # 1. Mandatory field checks
    if is_empty_or_null(raw_tx_id):
        return False, "Missing or null mandatory field: transaction_id", None, None
    if is_empty_or_null(raw_acc_num):
        return False, "Missing or null mandatory field: account_number", None, None
    if is_empty_or_null(raw_timestamp):
        return False, "Missing or null mandatory field: timestamp", None, None
    if is_empty_or_null(raw_merchant):
        return False, "Missing or null mandatory field: merchant", None, None

    # 2. Amount validity check (must be numeric and strictly > 0)
    if is_empty_or_null(raw_amount):
        return False, "Missing or null mandatory field: amount", None, None
    try:
        amount_val = float(raw_amount)
        if amount_val <= 0:
            return False, f"Invalid amount ({amount_val}): must be greater than 0", None, None
    except (ValueError, TypeError):
        return False, f"Malformed amount value: {raw_amount}", None, None

    # 3. Timestamp format check
    try:
        parsed_timestamp = datetime.fromisoformat(str(raw_timestamp).strip())
    except (ValueError, TypeError):
        return False, f"Invalid timestamp format: {raw_timestamp}", None, None

    # 4. Duplicate ID check
    tx_id_str = str(raw_tx_id).strip()
    if seen_batch_ids is not None and tx_id_str in seen_batch_ids:
        return False, f"Duplicate transaction_id '{tx_id_str}' found in current batch", None, None
    if existing_db_ids is not None and tx_id_str in existing_db_ids:
        return False, f"Duplicate transaction_id '{tx_id_str}' already exists in PostgreSQL database", None, None

    return True, None, amount_val, parsed_timestamp


def run_etl(csv_path: str = CSV_FILE) -> dict:
    print(f"[INFO] Starting ETL Pipeline, extracting from '{csv_path}'...")

    # Ensure tables exist in the target database
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[WARNING] Table verification check: {exc}")

    # --- Phase 1: Extract ---
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        msg = f"Could not find '{csv_path}'. Please run generate_mock_data.py first."
        print(f"[ERROR] {msg}")
        return {
            "status": "error",
            "message": msg,
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
        }
    except Exception as exc:
        msg = f"Error reading '{csv_path}': {exc}"
        print(f"[ERROR] {msg}")
        return {
            "status": "error",
            "message": msg,
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
        }

    print(f"[INFO] Successfully extracted {len(df)} rows from '{csv_path}'.")

    db = SessionLocal()

    total_processed = 0
    total_successful = 0
    total_failed = 0

    seen_batch_ids = set()

    try:
        # Pre-load existing transaction_ids from PostgreSQL to check duplicates efficiently
        existing_db_ids = {
            row[0] for row in db.query(Transaction.transaction_id).all()
        }
        print(f"[INFO] Found {len(existing_db_ids)} existing transactions in PostgreSQL.")

        # --- Phase 2: Transform & Validate & Phase 3: Load ---
        for index, row in df.iterrows():
            total_processed += 1

            row_dict = row.to_dict()
            raw_payload_str = json.dumps(row_dict, default=str)

            is_valid, error_reason, amount_val, parsed_timestamp = validate_transaction_row(
                row=row_dict,
                seen_batch_ids=seen_batch_ids,
                existing_db_ids=existing_db_ids,
            )

            # --- Phase 3: Load into PostgreSQL ---
            if not is_valid:
                total_failed += 1
                error_log = ErrorLog(
                    raw_payload=raw_payload_str,
                    error_message=error_reason,
                    logged_at=datetime.utcnow(),
                )
                db.add(error_log)
            else:
                raw_tx_id = row.get("transaction_id")
                raw_acc_num = row.get("account_number")
                raw_currency = row.get("currency")
                raw_merchant = row.get("merchant")

                tx_id_str = str(raw_tx_id).strip()
                currency_str = str(raw_currency).strip() if not is_empty_or_null(raw_currency) else "USD"
                merchant_str = str(raw_merchant).strip()

                transaction_record = Transaction(
                    transaction_id=tx_id_str,
                    account_number=str(raw_acc_num).strip(),
                    amount=amount_val,
                    currency=currency_str,
                    merchant=merchant_str,
                    status="SUCCESS",
                    timestamp=parsed_timestamp,
                )
                db.add(transaction_record)
                seen_batch_ids.add(tx_id_str)
                existing_db_ids.add(tx_id_str)
                total_successful += 1

        # Commit all transactions and error logs
        db.commit()

        # Summary Log
        print("\n" + "=" * 45)
        print("ETL PIPELINE EXECUTION SUMMARY")
        print("=" * 45)
        print(f"Total Processed : {total_processed}")
        print(f"Total Successful: {total_successful}")
        print(f"Total Failed    : {total_failed}")
        print("=" * 45)

        return {
            "status": "success",
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
        }

    except SQLAlchemyError as db_err:
        db.rollback()
        print(f"[ERROR] Database error during ETL execution: {db_err}")
        return {
            "status": "error",
            "message": str(db_err),
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
        }
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Unexpected error during ETL execution: {exc}")
        return {
            "status": "error",
            "message": str(exc),
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
        }
    finally:
        db.close()


if __name__ == "__main__":
    run_etl()
