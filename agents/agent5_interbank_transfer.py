from __future__ import annotations

import uuid
from typing import Any, Dict


class Agent5InterbankTransfer:
    """Agent 5: prepares transfer metadata from dataset fields without executing any transfer."""

    def run(
        self,
        drawer_bank: str,
        payee_bank: str,
        amount: float,
        allow_transfer: bool,
        cheque_number: str,
        account_valid: bool = True,
        drawer_ifsc: str = "",
        payee_ifsc: str = "",
    ) -> Dict[str, Any]:
        same_bank = (drawer_bank or "").strip().lower() == (payee_bank or "").strip().lower()
        if drawer_ifsc and payee_ifsc:
            same_bank = same_bank or drawer_ifsc[:4].lower() == payee_ifsc[:4].lower()
        transfer_mode = "INTERNAL" if same_bank else "NEFT"
        txn_ref = f"TXN-{transfer_mode[:2]}-{cheque_number}-{uuid.uuid4().hex[:6].upper()}"

        return {
            "status": "PASS",
            "confidence": 0.90 if account_valid else 0.45,
            "transfer_possible": bool(account_valid),
            "transfer_executed": False,
            "transfer_type": transfer_mode,
            "transaction_ref": txn_ref,
            "message": "Transfer ready, awaiting approval" if account_valid else "Transfer not ready until account verification succeeds",
            "details": {
                "transfer_possible": bool(account_valid),
                "transfer_executed": False,
                "transfer_type": transfer_mode,
                "transaction_ref": txn_ref,
                "same_bank": same_bank,
                "allow_transfer": allow_transfer,
            },
            "issues": [] if account_valid else ["Transfer cannot be prepared because account verification failed."],
        }
