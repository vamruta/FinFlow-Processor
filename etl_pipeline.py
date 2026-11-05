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


def run_etl():
    print(f"[INFO] Starting ETL Pipeline, extracting from '{CSV_FILE}'...")

    # Ensure tables exist in the target database
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[WARNING] Table verification check: {exc}")

    # --- Phase 1: Extract ---
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"[ERROR] Could not find '{CSV_FILE}'. Please run generate_mock_data.py first.")
        return
    except Exception as exc:
        print(f"[ERROR] Error reading '{CSV_FILE}': {exc}")
        return

    print(f"[INFO] Successfully extracted {len(df)} rows from '{CSV_FILE}'.")

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

            raw_tx_id = row.get("transaction_id")
            raw_acc_num = row.get("account_number")
            raw_amount = row.get("amount")
            raw_currency = row.get("currency")
            raw_merchant = row.get("merchant")
            raw_timestamp = row.get("timestamp")

            error_reason = None
            amount_val = None
            parsed_timestamp = None

            # 1. Check mandatory fields (transaction_id, account_number, timestamp)
            if is_empty_or_null(raw_tx_id):
                error_reason = "Missing or null mandatory field: transaction_id"
            elif is_empty_or_null(raw_acc_num):
                error_reason = "Missing or null mandatory field: account_number"
            elif is_empty_or_null(raw_timestamp):
                error_reason = "Missing or null mandatory field: timestamp"
            elif is_empty_or_null(raw_merchant):
                error_reason = "Missing or null mandatory field: merchant"

            # 2. Check amount validity (must be numeric and > 0)
            elif is_empty_or_null(raw_amount):
                error_reason = "Missing or null mandatory field: amount"
            else:
                try:
                    amount_val = float(raw_amount)
                    if amount_val <= 0:
                        error_reason = f"Invalid amount ({amount_val}): must be greater than 0"
                except (ValueError, TypeError):
                    error_reason = f"Malformed amount value: {raw_amount}"

            # 3. Check timestamp validity
            if not error_reason:
                try:
                    parsed_timestamp = datetime.fromisoformat(str(raw_timestamp).strip())
                except (ValueError, TypeError):
                    error_reason = f"Invalid timestamp format: {raw_timestamp}"

            # 4. Check for duplicate transaction_id
            if not error_reason:
                tx_id_str = str(raw_tx_id).strip()
                if tx_id_str in seen_batch_ids:
                    error_reason = f"Duplicate transaction_id '{tx_id_str}' found in current batch"
                elif tx_id_str in existing_db_ids:
                    error_reason = f"Duplicate transaction_id '{tx_id_str}' already exists in PostgreSQL database"

            # --- Phase 3: Load into PostgreSQL ---
            if error_reason:
                total_failed += 1
                error_log = ErrorLog(
                    raw_payload=raw_payload_str,
                    error_message=error_reason,
                    logged_at=datetime.utcnow(),
                )
                db.add(error_log)
            else:
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

    except SQLAlchemyError as db_err:
        db.rollback()
        print(f"[ERROR] Database error during ETL execution: {db_err}")
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Unexpected error during ETL execution: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    run_etl()
