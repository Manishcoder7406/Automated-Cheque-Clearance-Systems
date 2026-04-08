from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from bank_env.models import Action, Observation, State
from bank_env.reward import calculate_reward, derive_expected_action
from bank_env.tasks.easy import get_cases as get_easy_cases
from bank_env.tasks.hard import get_cases as get_hard_cases
from bank_env.tasks.medium import get_cases as get_medium_cases
from bank_env.vision.cheque_processor import ChequeProcessor


class BankChequeClearingEnv:
    """
    Hackathon-ready environment with a single-step decision per cheque case.
    Compatible with reset(), step(), and state() style APIs.
    """

    def __init__(self, difficulty: str = "easy", seed: Optional[int] = None) -> None:
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        self.current_state: Optional[State] = None
        self.processor = ChequeProcessor(seed=seed)
        self.last_case_details: Dict[str, Any] = {}

    def reset(
        self,
        difficulty: Optional[str] = None,
        image_path: Optional[str] = None,
        signature_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if difficulty is not None:
            self.difficulty = difficulty

        if image_path is not None:
            processed_case = self.processor.process_cheque(image_path, signature_path=signature_path)
            observation = Observation(**processed_case["state"])
            case_label = f"image_case:{Path(image_path).name}"
            self.last_case_details = processed_case
            recommended_action = Action(processed_case["final_decision"])
        else:
            observation, case_label = self._generate_case()
            self.last_case_details = {
                "mode": "simulated",
                "image_path": None,
                "account_number": None,
                "account_name": None,
                "cheque_amount": observation.cheque_amount,
                "account_balance": observation.account_balance,
                "data_valid": True,
                "signature_score": 1.0 if observation.signature_valid else 0.0,
                "signature_valid": observation.signature_valid,
                "account_valid": observation.account_valid,
                "fraud_score": observation.fraud_score,
                "transfer_status": observation.transfer_status,
                "agent_outputs": {
                    "data_validation": {"agent": "Cheque Data Validation Agent", "data_valid": True},
                    "signature_verification": {
                        "agent": "Signature Verification Agent",
                        "signature_valid": observation.signature_valid,
                        "signature_score": 1.0 if observation.signature_valid else 0.0,
                    },
                    "account_validation": {"agent": "Account Validation Agent", "account_valid": observation.account_valid},
                    "balance_behavior": {
                        "agent": "Balance & Behavior Agent",
                        "balance_ok": observation.account_balance >= observation.cheque_amount,
                        "fraud_score": observation.fraud_score,
                    },
                    "transfer": {"agent": "Interbank Transfer Agent", "transfer_status": observation.transfer_status},
                    "decision": {"agent": "Decision Agent", "final_decision": "APPROVE", "confidence": 0.75},
                },
            }
            recommended_action = derive_expected_action(observation)
        self.current_state = State(
            observation=observation,
            difficulty=self.difficulty,
            case_label=case_label,
            recommended_action=recommended_action,
        )
        return observation.to_dict()

    def step(self, action: Action | str) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        if self.current_state is None:
            raise RuntimeError("Environment must be reset before calling step().")
        if self.current_state.done:
            raise RuntimeError("Episode already finished. Call reset() to start a new case.")

        normalized_action = Action(action)
        expected_action = self.current_state.recommended_action
        reward = calculate_reward(normalized_action, expected_action)

        self.current_state.step_count += 1
        self.current_state.done = True

        info = {
            "difficulty": self.current_state.difficulty,
            "case_label": self.current_state.case_label,
            "expected_action": expected_action.value,
            "chosen_action": normalized_action.value,
            "correct": normalized_action == expected_action,
        }
        info.update(self.last_case_details)
        return self.current_state.observation.to_dict(), reward, True, info

    def state(self) -> Dict[str, Any]:
        if self.current_state is None:
            raise RuntimeError("Environment state is empty. Call reset() first.")
        payload = self.current_state.to_dict()
        payload["case_details"] = self.last_case_details
        return payload

    def _generate_case(self) -> tuple[Observation, str]:
        if self.difficulty == "easy":
            cases = get_easy_cases()
        elif self.difficulty == "medium":
            cases = get_medium_cases()
        elif self.difficulty == "hard":
            cases = get_hard_cases()
        else:
            raise ValueError(f"Unsupported difficulty: {self.difficulty}")

        case = self.rng.choice(cases)
        issues = case["ground_truth"]["issues"]
        obs = Observation(
            cheque_amount=case["record"]["amount_digits"],
            account_balance=case["record"]["amount_digits"] * 2.0 if issues.get("balance_ok", True) else case["record"]["amount_digits"] * 0.5,
            data_valid=issues.get("data_valid", True),
            signature_valid=issues.get("signature_valid", True),
            account_valid=issues.get("account_valid", True),
            fraud_score=0.1 if case["ground_truth"]["final_decision"] == "APPROVED" else 0.8,
            transfer_status="SUCCESS" if issues.get("transfer_success", True) else "FAILED"
        )
        return obs, f"simulated_{self.difficulty}_{case.get('cheque_id', 'unknown')}"
