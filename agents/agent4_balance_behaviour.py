from __future__ import annotations

import hashlib
from random import Random
from typing import Any, Dict


class Agent4BalanceBehaviour:
    """Agent 4: dataset-backed balance simulation and risk behavior."""

    def run(self, amount: float, account_record: Dict[str, Any] | None) -> Dict[str, Any]:
        if account_record is None:
            return {
                "status": "FAIL",
                "confidence": 0.0,
                "details": {"reason": "No matched dataset record available for balance simulation."},
                "risk_score": 1.0,
                "balance_ok": False,
                "issues": ["Unable to simulate balance because no dataset record was matched."],
            }

        seed_key = f"{account_record.get('account_number', '')}-{account_record.get('cheque_number', '')}-{amount}"
        seed = int(hashlib.sha256(seed_key.encode('utf-8')).hexdigest()[:8], 16)
        rng = Random(seed)

        balance = round(amount * rng.uniform(0.8, 1.8), 2)
        fraud_flag = False
        freeze_status = False
        bounced_history = rng.randint(0, 3)

        balance_ok = balance >= amount
        shortfall_ratio = max(0.0, amount - balance) / max(amount, 1)
        if balance_ok:
            status = "PASS"
        elif shortfall_ratio <= 0.15:
            status = "WARN"
        else:
            status = "FAIL"

        risk_score = round(min(1.0, 0.08 + bounced_history * 0.08 + (0.25 if not balance_ok else 0.0)), 2)
        issues: list[str] = []
        if not balance_ok:
            issues.append(f"Simulated balance is lower than cheque amount ({balance:,.0f} vs {amount:,.0f}).")
        if bounced_history >= 2:
            issues.append(f"Simulated bounced cheque history is elevated ({bounced_history}).")

        return {
            "status": status,
            "confidence": round(max(0.0, 1.0 - risk_score), 2),
            "details": {
                "balance": balance,
                "amount_requested": amount,
                "fraud_flag": fraud_flag,
                "freeze_status": freeze_status,
                "bounced_history": bounced_history,
                "source": "simulated_from_dataset",
                "issues": issues,
            },
            "risk_score": risk_score,
            "balance_ok": balance_ok,
            "issues": issues,
        }
