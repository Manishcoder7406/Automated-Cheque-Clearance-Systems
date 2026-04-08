from __future__ import annotations

from typing import Any, Dict

from bank_env.models import Action


class DecisionAgent:
    """
    Agent 6: combines all previous agent outputs into the final bank decision.
    """

    def run(self, *, outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        data_valid = outputs["data_validation"]["data_valid"]
        signature_valid = outputs["signature_verification"]["signature_valid"]
        account_valid = outputs["account_validation"]["account_valid"]
        balance_ok = outputs["balance_behavior"]["balance_ok"]
        fraud_score = outputs["balance_behavior"]["fraud_score"]
        transfer_status = outputs["transfer"]["transfer_status"]

        critical_failure = (
            not data_valid
            or not account_valid
            or not balance_ok
            or transfer_status == "FAILED"
        )

        if critical_failure:
            final_decision = Action.REJECT.value
        elif fraud_score > 0.7 or not signature_valid:
            final_decision = Action.FLAG.value
        else:
            final_decision = Action.APPROVE.value

        confidence = 0.45
        confidence += 0.15 if data_valid else -0.1
        confidence += 0.15 if account_valid else -0.1
        confidence += 0.1 if balance_ok else -0.1
        confidence += 0.15 if signature_valid else -0.05
        confidence += max(0.0, 0.2 - fraud_score * 0.2)
        confidence += 0.1 if transfer_status == "SUCCESS" else -0.1

        return {
            "agent": "Decision Agent",
            "final_decision": final_decision,
            "confidence": round(max(0.05, min(0.99, confidence)), 2),
        }
