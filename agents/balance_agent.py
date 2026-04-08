from __future__ import annotations

import random
from typing import Any, Dict


class BalanceBehaviorAgent:
    """
    Agent 4: evaluates balance sufficiency and simulated behavioral risk.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def run(
        self,
        *,
        cheque_amount: float,
        account_balance: float,
        signature_valid: bool,
        account_valid: bool,
        data_valid: bool,
        image_name: str,
    ) -> Dict[str, Any]:
        balance_ok = account_balance >= cheque_amount
        fraud_score = 0.12 + self.rng.uniform(0.0, 0.18)

        if not data_valid:
            fraud_score += 0.3
        if not account_valid:
            fraud_score += 0.35
        if not balance_ok:
            fraud_score += 0.22
        if not signature_valid:
            fraud_score += 0.45
        if cheque_amount > max(account_balance * 0.55, 3000.0):
            fraud_score += 0.1
        if image_name == "cheque2.jpg":
            fraud_score += 0.12
        if image_name == "cheque3.jpg":
            fraud_score += 0.35
        if image_name == "cheque3.png":
            fraud_score += 0.18

        return {
            "agent": "Balance & Behavior Agent",
            "balance_ok": balance_ok,
            "fraud_score": round(min(0.99, fraud_score), 2),
        }
