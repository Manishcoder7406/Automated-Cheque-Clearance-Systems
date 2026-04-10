from __future__ import annotations

from models import Action, Observation


def derive_expected_action(observation: Observation) -> Action:
    if observation.transfer_status == "FAILED" or not observation.account_valid:
        return Action.REJECT
    if observation.fraud_score >= 0.8:
        return Action.REJECT
    if not observation.data_valid or not observation.signature_valid:
        return Action.FLAG
    if observation.account_balance < observation.cheque_amount:
        return Action.FLAG
    return Action.APPROVE


def calculate_reward(action: Action, expected_action: Action) -> float:
    score_map = {
        Action.APPROVE: 1.0,
        Action.FLAG: 0.6,
        Action.REJECT: 0.0,
    }
    return round(0.5 * (1 - abs(score_map[action] - score_map[expected_action])), 2)
