from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict


class Action(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    FLAG = "FLAG"


@dataclass
class Observation:
    cheque_amount: float
    account_balance: float
    data_valid: bool
    signature_valid: bool
    account_valid: bool
    fraud_score: float
    transfer_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class State:
    observation: Observation
    difficulty: str
    case_label: str
    recommended_action: Action
    step_count: int = 0
    done: bool = False

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["recommended_action"] = self.recommended_action.value
        return payload
