from __future__ import annotations

from typing import Any, Dict


class Agent6Orchestrator:
    """Weighted orchestrator with APPROVED / REVIEW / REJECTED final decisions."""

    WEIGHTS = {
        "agent1": 0.25,
        "agent2": 0.25,
        "agent3": 0.15,
        "agent4": 0.20,
        "agent5": 0.15,
    }

    STATUS_SCORES = {
        "PASS": 1.0,
        "WARN": 0.6,
        "FAIL": 0.0,
    }

    APPROVED_THRESHOLD = 0.70
    REVIEW_THRESHOLD = 0.50

    FRIENDLY = {
        "agent1": "Cheque Data Validation",
        "agent2": "Signature Verification",
        "agent3": "Account Verification",
        "agent4": "Balance & Behaviour",
        "agent5": "Interbank Transfer",
    }

    def run(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        agent3_result = results.get("agent3", {})
        if agent3_result.get("status") == "FAIL":
            return {
                "status": "FAIL",
                "confidence": 0.0,
                "final_decision": "REJECTED",
                "details": {
                    "weighted_score": 0.0,
                    "weights": self.WEIGHTS,
                    "agent_scores": {"agent3": 0.0},
                    "reason_summary": ["Cheque not found in bank dataset"],
                },
            }

        agent2_result = results.get("agent2", {})
        if agent2_result.get("status") == "FAIL":
            return {
                "status": "FAIL",
                "confidence": 0.0,
                "final_decision": "REJECTED",
                "details": {
                    "weighted_score": 0.0,
                    "weights": self.WEIGHTS,
                    "agent_scores": {"agent2": 0.0},
                    "reason_summary": ["Signature not found or invalid"],
                },
            }

        weighted_score = 0.0
        agent_scores: Dict[str, float] = {}
        reasons: list[str] = []
        warn_count = 0
        fail_count = 0

        for agent_key, weight in self.WEIGHTS.items():
            result = results.get(agent_key, {})
            status = result.get("status", "FAIL")
            raw_score = self.STATUS_SCORES.get(status, 0.0)
            contribution = round(weight * raw_score, 4)

            weighted_score += contribution
            agent_scores[agent_key] = raw_score
            if status == "WARN":
                warn_count += 1
            elif status == "FAIL":
                fail_count += 1

            if status != "PASS":
                issues = result.get("issues", [])
                label = self.FRIENDLY.get(agent_key, agent_key)
                if issues:
                    reasons.extend(f"{label}: {iss}" for iss in issues)
                else:
                    reasons.append(f"{label} returned {status}.")

        weighted_score = round(min(1.0, weighted_score), 3)

        if weighted_score >= self.APPROVED_THRESHOLD:
            final_decision = "APPROVED"
        elif weighted_score >= self.REVIEW_THRESHOLD:
            final_decision = "REVIEW"
        else:
            final_decision = "REJECTED"

        cross_bank = not bool(results.get("agent5", {}).get("details", {}).get("same_bank", True))
        if final_decision == "APPROVED" and warn_count >= 2 and cross_bank:
            final_decision = "REVIEW"
        if fail_count >= 1 and warn_count >= 1 and weighted_score <= self.APPROVED_THRESHOLD:
            final_decision = "REJECTED"

        if not reasons:
            reasons.append("All agents passed with no issues.")

        return {
            "status": "PASS" if final_decision == "APPROVED" else "WARN" if final_decision == "REVIEW" else "FAIL",
            "confidence": weighted_score,
            "final_decision": final_decision,
            "details": {
                "weighted_score": weighted_score,
                "weights": self.WEIGHTS,
                "agent_scores": agent_scores,
                "reason_summary": reasons,
            },
        }
