from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SIGNATURE_DIR = PACKAGE_ROOT / "data" / "signatures"
EXTERNAL_CHEQUE_DIR = Path(r"E:\cheque")

MOCK_ACCOUNTS = {
    "911010049001545": {
        "name": "Rajarshi Pal",
        "account_number": "911010049001545",
        "bank": "Axis Bank",
        "ifsc": "UTIB0000426",
        "branch": "Mehdipatnam",
        "balance": 350000.0,
        "fraud_flag": False,
        "freeze_status": False,
        "bounced_history": 0,
        "active": True,
        "signature_path": str(EXTERNAL_CHEQUE_DIR / "cheque1_signature.jpg"),
    },
    "ACC001": {
        "name": "Harman",
        "account_number": "ACC001",
        "bank": "Axis Bank",
        "ifsc": "UTIB0000426",
        "branch": "Hyderabad",
        "balance": 10000.0,
        "fraud_flag": False,
        "freeze_status": False,
        "bounced_history": 0,
        "active": True,
        "signature_path": str(SIGNATURE_DIR / "harman_ref.png"),
    },
    "ACC002": {
        "name": "Rahul",
        "account_number": "ACC002",
        "bank": "Axis Bank",
        "ifsc": "UTIB0000426",
        "branch": "Hyderabad",
        "balance": 5000.0,
        "fraud_flag": False,
        "freeze_status": False,
        "bounced_history": 1,
        "active": True,
        "signature_path": str(SIGNATURE_DIR / "rahul_ref.png"),
    },
    "ACC004": {
        "name": "Priya Sharma",
        "account_number": "ACC004",
        "bank": "HDFC Bank",
        "ifsc": "HDFC0001200",
        "branch": "Bengaluru",
        "balance": 250000.0,
        "fraud_flag": True,
        "freeze_status": False,
        "bounced_history": 3,
        "active": True,
        "signature_path": str(SIGNATURE_DIR / "rahul_ref.png"),
    },
    "ACC005": {
        "name": "Neha Verma",
        "account_number": "ACC005",
        "bank": "ICICI Bank",
        "ifsc": "ICIC0004432",
        "branch": "Mumbai",
        "balance": 90000.0,
        "fraud_flag": True,
        "freeze_status": True,
        "bounced_history": 5,
        "active": False,
        "signature_path": str(SIGNATURE_DIR / "harman_ref.png"),
    },
}
