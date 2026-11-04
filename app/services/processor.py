from typing import Any, Dict, List
import pandas as pd


class FinancialProcessorService:
    @staticmethod
    def calculate_summary(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process financial transaction records using pandas to calculate analytics."""
        if not transactions:
            return {
                "total_volume": 0.0,
                "transaction_count": 0,
                "average_amount": 0.0,
                "by_category": {},
            }

        df = pd.DataFrame(transactions)

        return {
            "total_volume": round(float(df["amount"].sum()), 2),
            "transaction_count": int(len(df)),
            "average_amount": round(float(df["amount"].mean()), 2),
            "by_category": {
                k: round(float(v), 2)
                for k, v in df.groupby("category")["amount"].sum().to_dict().items()
            },
        }
