from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Optional

from agents import (
    AccountValidationAgent,
    BalanceBehaviorAgent,
    ChequeDataValidationAgent,
    DecisionAgent,
    InterbankTransferAgent,
    SignatureVerificationAgent,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
CHEQUES_DIR = DATA_DIR / "cheques"
SIGNATURES_DIR = DATA_DIR / "signatures"
EXTERNAL_CHEQUE_DIR = Path(r"E:\cheque")

ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "ACC001": {
        "name": "Harman",
        "balance": 10000.0,
        "signature_path": str(SIGNATURES_DIR / "harman_ref.png"),
        "active": True,
    },
    "ACC002": {
        "name": "Rahul",
        "balance": 5000.0,
        "signature_path": str(SIGNATURES_DIR / "rahul_ref.png"),
        "active": True,
    },
    "911010049001545": {
        "name": "Rajarshi Pal",
        "balance": 350000.0,
        "signature_path": str(EXTERNAL_CHEQUE_DIR / "cheque1_signature.jpg"),
        "active": True,
    },
}

DEMO_CHEQUE_DATA: Dict[str, Dict[str, Any]] = {
    "cheque1.png": {
        "account_number": "ACC001",
        "cheque_amount": 2400.0,
        "signature_path": str(CHEQUES_DIR / "cheque1_signature.png"),
        "account_holder_name": "Harman",
    },
    "cheque2.png": {
        "account_number": "ACC002",
        "cheque_amount": 6200.0,
        "signature_path": str(CHEQUES_DIR / "cheque2_signature.png"),
        "account_holder_name": "Rahul",
    },
    "cheque3.png": {
        "account_number": "ACC001",
        "cheque_amount": 1800.0,
        "signature_path": str(CHEQUES_DIR / "cheque3_signature.png"),
        "account_holder_name": "Harman",
    },
    "cheque1.jpg": {
        "account_number": "911010049001545",
        "cheque_amount": 210500.0,
        "signature_path": str(EXTERNAL_CHEQUE_DIR / "cheque1_signature.jpg"),
        "payee_name": "Amita Kadam",
        "account_holder_name": "Rajarshi Pal",
        "source": "user_sample",
    },
    "cheque2.jpg": {
        "account_number": "911010049001545",
        "cheque_amount": 125000.0,
        "signature_path": str(EXTERNAL_CHEQUE_DIR / "cheque2_signature.jpg"),
        "payee_name": "Sunil Kumar",
        "account_holder_name": "Rajarshi Pal",
        "source": "user_sample",
    },
    "cheque3.jpg": {
        "account_number": "911010049001545",
        "cheque_amount": 42000000.0,
        "signature_path": str(EXTERNAL_CHEQUE_DIR / "cheque3_signature.jpg"),
        "payee_name": "Chahat Thawa",
        "account_holder_name": "Rajarshi Pal",
        "source": "user_sample",
    },
}


class ChequeProcessor:
    """
    Demo cheque processor for hackathon workflows.
    Field extraction is hardcoded by filename, while signature checking
    uses actual image similarity scoring.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.data_agent = ChequeDataValidationAgent()
        self.signature_agent = SignatureVerificationAgent()
        self.account_agent = AccountValidationAgent()
        self.balance_agent = BalanceBehaviorAgent(seed=seed)
        self.transfer_agent = InterbankTransferAgent()
        self.decision_agent = DecisionAgent()

    def process_cheque(self, image_path: str, signature_path: Optional[str] = None) -> Dict[str, Any]:
        image_name = Path(image_path).name
        extracted_data = self.extract_cheque_data(image_path, signature_path=signature_path)

        account_number = extracted_data["account_number"]
        cheque_amount = extracted_data["cheque_amount"]
        account = ACCOUNTS.get(account_number)
        account_balance = float(account["balance"]) if account else 0.0
        account_name = account["name"] if account else "Unknown"
        reference_signature_path = account["signature_path"] if account else None

        data_validation = self.data_agent.run(extracted_data, ACCOUNTS)
        signature_verification = self.signature_agent.run(
            cheque_signature_path=extracted_data["signature_path"],
            reference_signature_path=reference_signature_path,
        )
        account_validation = self.account_agent.run(account_number, ACCOUNTS)
        balance_behavior = self.balance_agent.run(
            cheque_amount=cheque_amount,
            account_balance=account_balance,
            signature_valid=signature_verification["signature_valid"],
            account_valid=account_validation["account_valid"],
            data_valid=data_validation["data_valid"],
            image_name=image_name,
        )
        transfer_result = self.transfer_agent.run(
            data_valid=data_validation["data_valid"],
            account_valid=account_validation["account_valid"],
            balance_ok=balance_behavior["balance_ok"],
            fraud_score=balance_behavior["fraud_score"],
        )
        agent_outputs = {
            "data_validation": data_validation,
            "signature_verification": signature_verification,
            "account_validation": account_validation,
            "balance_behavior": balance_behavior,
            "transfer": transfer_result,
        }
        decision_result = self.decision_agent.run(outputs=agent_outputs)

        state = {
            "cheque_amount": cheque_amount,
            "account_balance": account_balance,
            "data_valid": data_validation["data_valid"],
            "signature_valid": signature_verification["signature_valid"],
            "account_valid": account_validation["account_valid"],
            "fraud_score": balance_behavior["fraud_score"],
            "transfer_status": transfer_result["transfer_status"],
        }

        return {
            "mode": "image",
            "image_path": str(Path(image_path)),
            "account_number": account_number,
            "account_name": account_name,
            "cheque_amount": cheque_amount,
            "account_balance": account_balance,
            "signature_path": extracted_data["signature_path"],
            "reference_signature_path": reference_signature_path,
            "fraud_score": balance_behavior["fraud_score"],
            "payee_name": extracted_data.get("payee_name", "Unknown"),
            "data_source": extracted_data.get("source", "demo"),
            "data_valid": data_validation["data_valid"],
            "signature_valid": signature_verification["signature_valid"],
            "signature_score": signature_verification["signature_score"],
            "account_valid": account_validation["account_valid"],
            "balance_ok": balance_behavior["balance_ok"],
            "transfer_status": transfer_result["transfer_status"],
            "final_decision": decision_result["final_decision"],
            "decision_confidence": decision_result["confidence"],
            "agent_outputs": {
                **agent_outputs,
                "decision": decision_result,
            },
            "state": state,
        }

    def extract_cheque_data(self, image_path: str, signature_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Hardcoded extraction for demo images. This keeps the pipeline simple
        while still exercising the full environment with local image files.
        """
        image_name = Path(image_path).name
        if image_name not in DEMO_CHEQUE_DATA:
            raise ValueError(
                f"Unsupported cheque image '{image_name}'. "
                "Use one of the sample images in bank_env/data/cheques/ or e:\\cheque."
            )
        data = dict(DEMO_CHEQUE_DATA[image_name])
        if signature_path is not None:
            data["signature_path"] = signature_path
        return data

    def list_known_samples(self) -> list[Dict[str, str]]:
        samples: list[Dict[str, str]] = []
        for image_name, data in DEMO_CHEQUE_DATA.items():
            image_path = CHEQUES_DIR / image_name
            if image_name.endswith(".jpg"):
                image_path = EXTERNAL_CHEQUE_DIR / image_name
            samples.append(
                {
                    "label": image_name,
                    "image_path": str(image_path),
                    "signature_path": data["signature_path"],
                }
            )
        return samples
