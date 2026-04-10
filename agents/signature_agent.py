from __future__ import annotations

from typing import Any, Dict

from vision.signature_verifier import verify_signature


class SignatureVerificationAgent:
    """
    Agent 2: verifies cheque signature against the stored reference image.
    """

    def run(self, cheque_signature_path: str, reference_signature_path: str | None) -> Dict[str, Any]:
        if reference_signature_path is None:
            return {
                "agent": "Signature Verification Agent",
                "signature_valid": False,
                "signature_score": 0.0,
                "threshold": 0.7,
            }

        result = verify_signature(
            cheque_signature_path=cheque_signature_path,
            reference_signature_path=reference_signature_path,
        )
        result["agent"] = "Signature Verification Agent"
        return result
