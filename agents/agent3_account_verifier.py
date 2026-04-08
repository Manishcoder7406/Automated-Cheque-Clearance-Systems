from __future__ import annotations

from typing import Any, Dict

import pandas as pd


class Agent3AccountVerifier:
    """Agent 3: strict dataset-driven account verification (exact match only)."""

    def run(self, extracted_data: Dict[str, Any], dataset_df: pd.DataFrame | None) -> Dict[str, Any]:
        if dataset_df is None or dataset_df.empty:
            return {
                "status": "FAIL",
                "confidence": 0.0,
                "matched_record": None,
                "matched_account": None,
                "match_type": "none",
                "account_valid": False,
                "issues": ["Dataset is missing, so account verification could not run."],
            }

        extracted_account = str(extracted_data.get("account_number") or "").strip()
        extracted_ifsc = str(extracted_data.get("ifsc") or "").strip()
        exact_match = dataset_df[
            (dataset_df["account_number"].astype(str) == extracted_account)
            & (dataset_df["ifsc_code"].astype(str).str.lower() == extracted_ifsc.lower())
        ]
        if not exact_match.empty:
            matched_record = exact_match.iloc[0].to_dict()
            return {
                "status": "PASS",
                "confidence": 0.95,
                "matched_record": matched_record,
                "matched_account": matched_record,
                "match_type": "exact",
                "account_valid": True,
                "issues": [],
            }

        return {
            "status": "FAIL",
            "confidence": 0.0,
            "matched_record": None,
            "matched_account": None,
            "match_type": "none",
            "account_valid": False,
            "issues": ["No matching record found in dataset"],
        }
