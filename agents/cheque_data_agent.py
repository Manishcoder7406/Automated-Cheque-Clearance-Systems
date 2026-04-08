from __future__ import annotations

from typing import Any, Dict


class ChequeDataValidationAgent:
    """
    Agent 1: validates extracted cheque metadata against the simulated bank dataset.
    """

    def run(self, extracted_data: Dict[str, Any], accounts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        account_number = extracted_data["account_number"]
        account = accounts.get(account_number)
        account_exists = account is not None
        name_matches = account_exists and extracted_data.get("account_holder_name", account["name"]) == account["name"]

        return {
            "agent": "Cheque Data Validation Agent",
            "data_valid": bool(account_exists and name_matches),
            "account_exists": account_exists,
            "name_matches": bool(name_matches),
        }
