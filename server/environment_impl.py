from __future__ import annotations

from pathlib import Path
from random import Random
from typing import Any, Dict, Optional

import cv2
import pandas as pd

from agents.agent1_cheque_validator import Agent1ChequeValidator
from agents.agent2_signature_verifier import Agent2SignatureVerifier
from agents.agent3_account_verifier import Agent3AccountVerifier
from agents.agent4_balance_behaviour import Agent4BalanceBehaviour
from agents.agent5_interbank_transfer import Agent5InterbankTransfer
from agents.agent6_orchestrator import Agent6Orchestrator
from tasks.easy import get_cases as get_easy_cases
from tasks.hard import get_cases as get_hard_cases
from tasks.medium import get_cases as get_medium_cases
from utils.extract_signatures import extract_signatures_from_pdf

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SIGNATURE_OUTPUT_DIR = PACKAGE_ROOT / "data" / "signatures"
TEMP_DIR = PACKAGE_ROOT / "data" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

STATUS_SCORES = {"PASS": 1.0, "WARN": 0.6, "FAIL": 0.0}
DECISION_SCORES = {"APPROVED": 1.0, "REVIEW": 0.6, "REJECTED": 0.0}


class BankChequeClearingEnv:
    """OpenEnv-compatible multi-agent cheque clearing environment."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = Random(seed)
        self.last_case: Optional[Dict[str, Any]] = None
        self.last_info: Dict[str, Any] = {}
        self.current_state: Dict[str, Any] = {}
        self.agent1 = Agent1ChequeValidator()
        self.agent2 = Agent2SignatureVerifier()
        self.agent3 = Agent3AccountVerifier()
        self.agent4 = Agent4BalanceBehaviour()
        self.agent5 = Agent5InterbankTransfer()
        self.agent6 = Agent6Orchestrator()
        self.cases_by_difficulty = {
            "easy": get_easy_cases(),
            "medium": get_medium_cases(),
            "hard": get_hard_cases(),
        }
        self.reset(seed=seed)

    def reset(self, seed: Optional[int] = None, **_: Any) -> dict:
        if seed is not None:
            self.rng.seed(seed)
        self.last_case = None
        self.last_info = {}
        self.current_state = {
            "cheque_id": "",
            "difficulty": "",
            "agent1_result": {},
            "agent2_result": {},
            "agent3_result": {},
            "agent4_result": {},
            "agent5_result": {},
            "agent6_result": {},
            "final_decision": "PENDING",
            "confidence": 0.0,
            "reward": 0.0,
            "done": False,
        }
        return dict(self.current_state)

    def step(self, action: dict) -> tuple:
        cheque_image_path = action.get("cheque_image_path")
        dataset_df: pd.DataFrame | None = action.get("dataset_df")
        if not cheque_image_path:
            raise ValueError("Missing action key: cheque_image_path")
        if dataset_df is None or dataset_df.empty:
            raise ValueError("Uploaded Excel dataset is required for this pipeline.")

        requested_difficulty = action.get("difficulty", "easy")
        if requested_difficulty not in self.cases_by_difficulty:
            raise ValueError(f"Unsupported difficulty: {requested_difficulty}")

        case = self._select_case(requested_difficulty, cheque_image_path)
        self.last_case = case
        resolved_signature_paths = action.get("signature_paths") or []
        if action.get("signature_pdf_path"):
            resolved_signature_paths = self._resolve_signature_database(action.get("signature_pdf_path"), None)

        agent1_result = self.agent1.run(cheque_image_path, case["record"])
        extracted_data = dict(agent1_result.get("extracted", {}))
        requested_amount = float(extracted_data.get("amount_digits") or case["record"]["amount_digits"])

        agent3_result = self.agent3.run(extracted_data, dataset_df)
        matched_record = agent3_result.get("matched_record")

        agent2_result = self.agent2.run(
            cheque_image_path=cheque_image_path,
            signature_paths=resolved_signature_paths or None,
        )
        agent4_result = self.agent4.run(requested_amount, matched_record)
        agent5_result = self.agent5.run(
            drawer_bank=str((matched_record or {}).get("bank_name") or extracted_data.get("bank_name") or case["record"].get("bank_name", "")),
            payee_bank=str(extracted_data.get("bank_name") or case["record"].get("payee_bank", "")),
            amount=requested_amount,
            allow_transfer=(agent4_result.get("status") != "FAIL") and agent3_result.get("account_valid", False),
            cheque_number=str(extracted_data.get("cheque_number") or case["record"]["cheque_number"]),
            account_valid=agent3_result.get("account_valid", False),
            drawer_ifsc=str((matched_record or {}).get("ifsc_code") or extracted_data.get("ifsc") or ""),
            payee_ifsc=str(extracted_data.get("ifsc") or ""),
        )
        orchestrator_result = self.agent6.run(
            {
                "agent1": agent1_result,
                "agent2": agent2_result,
                "agent3": agent3_result,
                "agent4": agent4_result,
                "agent5": agent5_result,
            }
        )

        reward = self.compute_reward(
            orchestrator_result["final_decision"],
            case["ground_truth"],
            {
                "agent1_result": agent1_result,
                "agent2_result": agent2_result,
                "agent3_result": agent3_result,
                "agent4_result": agent4_result,
                "agent5_result": agent5_result,
            },
        )

        self.current_state = {
            "cheque_id": case["cheque_id"],
            "difficulty": case["difficulty"],
            "agent1_result": agent1_result,
            "agent2_result": agent2_result,
            "agent3_result": agent3_result,
            "agent4_result": agent4_result,
            "agent5_result": agent5_result,
            "agent6_result": orchestrator_result,
            "final_decision": orchestrator_result["final_decision"],
            "confidence": orchestrator_result["confidence"],
            "reward": reward,
            "done": True,
        }

        self.last_info = {
            "ground_truth": case["ground_truth"],
            "record": case["record"],
            "cheque_image_path": cheque_image_path,
            "agent_outputs": {
                "agent1": agent1_result,
                "agent2": agent2_result,
                "agent3": agent3_result,
                "agent4": agent4_result,
                "agent5": agent5_result,
                "agent6": orchestrator_result,
            },
            "extracted_data": extracted_data,
            "matched_account_number": str((matched_record or {}).get("account_number", "")),
            "matched_account": matched_record,
            "known_case_match": case.get("known_case_match", False),
            "image_match_score": case.get("image_match_score", 0.0),
            "signature_paths_used": resolved_signature_paths,
            "issues": self._merge_issues(
                agent1_result,
                agent2_result,
                agent3_result,
                agent4_result,
                agent5_result,
                orchestrator_result,
            ),
        }
        return dict(self.current_state), reward, True, dict(self.last_info)

    def state(self) -> dict:
        payload = dict(self.current_state)
        payload["case"] = self.last_case
        payload["info"] = self.last_info
        return payload

    def compute_reward(self, final_decision: str, ground_truth: dict, results: dict) -> float:
        expected = self._expected_statuses(ground_truth)
        reward = 0.0

        for key, expected_status in expected.items():
            actual_status = results[key].get("status", "FAIL")
            reward += 0.2 * (1 - abs(STATUS_SCORES[actual_status] - STATUS_SCORES[expected_status]))

        expected_final = ground_truth["final_decision"]
        reward += 0.5 * (1 - abs(DECISION_SCORES[final_decision] - DECISION_SCORES[expected_final]))
        return round(reward, 2)

    def _expected_statuses(self, ground_truth: dict) -> dict:
        issues = ground_truth["issues"]
        return {
            "agent1_result": "PASS" if issues.get("data_valid", True) else "FAIL",
            "agent2_result": "PASS" if issues.get("signature_valid", True) else "FAIL",
            "agent3_result": "PASS" if issues.get("account_valid", True) else "FAIL",
            "agent4_result": "PASS" if issues.get("balance_ok", True) else "WARN",
            "agent5_result": "PASS",
        }

    def _merge_issues(self, *results: dict) -> list[str]:
        merged: list[str] = []
        for result in results:
            merged.extend(result.get("issues", []))
            details = result.get("details", {})
            if isinstance(details, dict):
                extra = details.get("issues", [])
                if isinstance(extra, list):
                    merged.extend(extra)
        return merged

    def _select_case(self, difficulty: str, cheque_image_path: str) -> dict:
        image_name = Path(cheque_image_path).name
        for known_difficulty, cases in self.cases_by_difficulty.items():
            for case in cases:
                if Path(case["cheque_image_path"]).name == image_name:
                    selected = dict(case)
                    selected["difficulty"] = known_difficulty
                    selected["known_case_match"] = True
                    return selected

        best_case: Optional[dict] = None
        best_score = -1.0
        for known_difficulty, cases in self.cases_by_difficulty.items():
            for case in cases:
                score = self._compare_cheque_images(cheque_image_path, case["cheque_image_path"])
                if score > best_score:
                    best_score = score
                    best_case = dict(case)
                    best_case["difficulty"] = known_difficulty

        if best_case is not None and best_score >= 0.75:
            best_case["known_case_match"] = True
            best_case["image_match_score"] = round(best_score, 3)
            best_case["uploaded_cheque_image_path"] = cheque_image_path
            return best_case

        selected = dict(self.cases_by_difficulty[difficulty][0])
        selected["cheque_image_path"] = cheque_image_path
        selected["known_case_match"] = False
        return selected

    @staticmethod
    def _compare_cheque_images(uploaded_path: str, reference_path: str) -> float:
        uploaded = cv2.imread(uploaded_path, cv2.IMREAD_GRAYSCALE)
        reference = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
        if uploaded is None or reference is None:
            return 0.0

        uploaded = cv2.resize(uploaded, (480, 220))
        reference = cv2.resize(reference, (480, 220))
        uploaded = cv2.GaussianBlur(uploaded, (5, 5), 0)
        reference = cv2.GaussianBlur(reference, (5, 5), 0)
        score = float(cv2.matchTemplate(uploaded, reference, cv2.TM_CCOEFF_NORMED).max())
        return max(0.0, min(1.0, score))

    def _resolve_signature_database(self, signature_pdf_path: Optional[str], account_record: Optional[dict]) -> list[str]:
        if signature_pdf_path:
            return extract_signatures_from_pdf(signature_pdf_path, str(SIGNATURE_OUTPUT_DIR))

        candidate_paths: list[str] = []
        candidate_paths.extend(str(path) for path in sorted(SIGNATURE_OUTPUT_DIR.glob("sig_*.png")))
        candidate_paths.extend(str(path) for path in sorted(SIGNATURE_OUTPUT_DIR.glob("*_ref.png")))
        if account_record and account_record.get("signature_path"):
            candidate_paths.append(account_record["signature_path"])

        deduped: list[str] = []
        seen: set[str] = set()
        for path in candidate_paths:
            if path not in seen and Path(path).exists():
                deduped.append(path)
                seen.add(path)
        return deduped
