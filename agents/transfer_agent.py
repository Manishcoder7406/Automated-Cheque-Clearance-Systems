from __future__ import annotations

from typing import Any, Dict


class InterbankTransferAgent:
    """
    Agent 5: simulates a downstream interbank transfer check.
    """

    def run(
        self,
        *,
        data_valid: bool,
        account_valid: bool,
        balance_ok: bool,
        fraud_score: float,
    ) -> Dict[str, Any]:
        transfer_status = "SUCCESS"
        if not data_valid or not account_valid or not balance_ok or fraud_score > 0.85:
            transfer_status = "FAILED"
        return {
            "agent": "Interbank Transfer Agent",
            "transfer_status": transfer_status,
        }
