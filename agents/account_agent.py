from __future__ import annotations

from typing import Any, Dict


class AccountValidationAgent:
    """
    Agent 3: checks whether the account exists and is active.
    """

    def run(self, account_number: str, accounts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        account = accounts.get(account_number)
        account_valid = bool(account and account.get("active", True))
        return {
            "agent": "Account Validation Agent",
            "account_valid": account_valid,
            "account_active": bool(account.get("active", True)) if account else False,
        }
