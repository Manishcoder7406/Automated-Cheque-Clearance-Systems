from __future__ import annotations

from bank_env.models import Action


class BaselineChequeAgent:
    """
    Rule-based baseline that mirrors a cautious bank operations analyst.
    It prefers rejecting hard violations, flags borderline cases, and
    approves only when signals are clean.
    """

    def act(self, observation: dict) -> Action:
        cheque_amount = observation["cheque_amount"]
        balance = observation["account_balance"]
        data_valid = observation["data_valid"]
        signature_valid = observation["signature_valid"]
        account_valid = observation["account_valid"]
        fraud_score = observation["fraud_score"]
        transfer_status = observation["transfer_status"]

        if not data_valid:
            return Action.REJECT
        if not account_valid:
            return Action.REJECT
        if transfer_status == "FAILED":
            return Action.REJECT
        if balance < cheque_amount:
            return Action.REJECT
        if fraud_score > 0.75:
            return Action.REJECT
        if not signature_valid and fraud_score >= 0.5:
            return Action.REJECT
        if not signature_valid or fraud_score >= 0.45:
            return Action.FLAG
        return Action.APPROVE
