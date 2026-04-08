from __future__ import annotations

import re
from difflib import SequenceMatcher, get_close_matches
from typing import Any, Dict

import cv2
import numpy as np
import pandas as pd
import pytesseract
from pytesseract import TesseractNotFoundError

WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT_PATH

MANDATORY_FIELDS = (
    "payee_name",
    "amount_digits",
    "amount_words",
    "date",
    "cheque_number",
)

PAYEE_HINTS = ("pay", "payee", "pay to")
AMOUNT_HINTS = ("rupees", "rupee", "lakh", "lakhs", "lacs", "thousand")
BANK_NAMES = ("Axis Bank", "HDFC Bank", "SBI", "ICICI Bank", "Kotak", "PNB", "Bank of Baroda")


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresholded = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    return cv2.resize(thresholded, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)


def _ocr(processed: np.ndarray) -> str:
    try:
        return pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
    except TesseractNotFoundError:
        return ""


def _ocr_confidence(processed: np.ndarray) -> float:
    try:
        data = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT,
        )
    except TesseractNotFoundError:
        return 0.0

    scores: list[float] = []
    for raw_score in data.get("conf", []):
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        if score >= 0:
            scores.append(score)

    if not scores:
        return 0.0
    return round(sum(scores) / (len(scores) * 100.0), 2)


def _clean_ocr_text(text: str) -> str:
    cleaned = text.lower()
    for token in ("|", "—", "_", "=", "%"):
        cleaned = cleaned.replace(token, " ")
    cleaned = re.sub(r"[^a-z0-9,./\-\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _clean_ocr_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.lower()
        for token in ("|", "—", "_", "=", "%"):
            line = line.replace(token, " ")
        line = re.sub(r"[^a-z0-9,./\-\s]", " ", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _normalize_amount_token(token: str) -> str:
    replacements = str.maketrans(
        {
            "o": "0",
            "O": "0",
            "l": "1",
            "L": "1",
            "i": "1",
            "I": "1",
            "s": "5",
            "S": "5",
            "b": "8",
            "B": "8",
        }
    )
    normalized = token.translate(replacements)
    normalized = re.sub(r"[^\d]", "", normalized)
    return normalized


def _extract_amount_digits(cleaned_text: str, lines: list[str]) -> float | None:
    candidate_values: list[int] = []
    for line in lines or [cleaned_text]:
        if any(blocker in line for blocker in ("a/c", "account", "ifsc", "micr")):
            continue
        for match in re.findall(r"\d[\d,\.]{2,}", line):
            digits = _normalize_amount_token(match)
            if len(digits) >= 3:
                candidate_values.append(int(digits))
    if not candidate_values:
        return None
    return float(max(candidate_values))


def _extract_date(cleaned_text: str) -> str | None:
    match = re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", cleaned_text)
    return match.group(0).replace("-", "/") if match else None


def _extract_cheque_number(cleaned_text: str) -> str | None:
    micr_groups = re.findall(r"\b\d{6}\b", cleaned_text)
    if micr_groups:
        return micr_groups[-1]
    digits = re.findall(r"\d", cleaned_text)
    if len(digits) >= 6:
        return "".join(digits[-6:])
    return None


def _extract_payee_name(lines: list[str]) -> str | None:
    best_line: str | None = None
    best_score = 0.0

    for index, line in enumerate(lines):
        line_score = max((_similarity(line, hint) for hint in PAYEE_HINTS), default=0.0)
        token_score = max((_similarity(token, hint) for token in line.split() for hint in PAYEE_HINTS), default=0.0)
        score = max(line_score, token_score)
        if score > best_score:
            best_score = score
            candidate = re.sub(r"\bpay(?:ee| to)?\b", " ", line).strip(" -:")
            if candidate:
                best_line = candidate
            elif index + 1 < len(lines):
                best_line = lines[index + 1].strip(" -:")

    if best_score > 0.5 and best_line:
        best_line = re.sub(r"\b(or bearer|bearer|utr)\b.*$", "", best_line).strip(" -:")
        return best_line or None

    fallback = max(lines, key=len, default="")
    return fallback or None


def _normalize_amount_words_line(line: str) -> str:
    replacements = {
        "lacks": "lakh",
        "lakhs": "lakh",
        "lacs": "lakh",
        "lac": "lakh",
        "rues": "rupees",
        "rupes": "rupees",
        "rupess": "rupees",
    }
    normalized = line
    for source, target in replacements.items():
        normalized = re.sub(rf"\b{source}\b", target, normalized)
    return normalized


def _extract_amount_words(lines: list[str]) -> str | None:
    best_line: str | None = None
    best_score = 0.0

    for line in lines:
        normalized = _normalize_amount_words_line(line)
        score = 0.0
        for token in normalized.split():
            score = max(score, max((_similarity(token, hint) for hint in AMOUNT_HINTS), default=0.0))
        if any(hint in normalized for hint in ("rupees", "lakh", "thousand")):
            score = max(score, 0.8)
        if score > best_score:
            best_score = score
            best_line = normalized

    return best_line if best_score > 0.5 else None


def _extract_bank_name(cleaned_text: str) -> str | None:
    for bank in BANK_NAMES:
        if bank.lower() in cleaned_text:
            return bank
    return None


def _select_dataset_record(raw_extracted: Dict[str, Any], dataset_df: pd.DataFrame) -> Dict[str, Any] | None:
    if dataset_df.empty:
        return None

    best_row: Dict[str, Any] | None = None
    best_score = -1.0
    raw_payee = str(raw_extracted.get("payee_name") or "").strip()
    raw_cheque = str(raw_extracted.get("cheque_number") or "").strip()
    raw_account = str(raw_extracted.get("account_number") or "").strip()
    raw_ifsc = str(raw_extracted.get("ifsc") or "").strip()
    raw_amount = float(raw_extracted.get("amount_digits") or 0)

    for _, row in dataset_df.iterrows():
        score = 0.0
        cheque_number = str(row.get("cheque_number", "") or "").strip()
        account_number = str(row.get("account_number", "") or "").strip()
        ifsc_code = str(row.get("ifsc_code", "") or "").strip()
        payee_name = str(row.get("payee_name", "") or "").strip()
        amount_numbers = float(row.get("amount_numbers", 0) or 0)

        if raw_cheque and cheque_number and raw_cheque == cheque_number:
            score += 4.0
        if raw_account and account_number and raw_account == account_number:
            score += 3.0
        if raw_ifsc and ifsc_code and raw_ifsc.lower() == ifsc_code.lower():
            score += 2.0
        if raw_payee and payee_name:
            score += _similarity(raw_payee.lower(), payee_name.lower()) * 2.0
        if raw_amount and amount_numbers:
            variance = abs(raw_amount - amount_numbers) / max(amount_numbers, 1)
            score += max(0.0, 1.0 - variance)

        if score > best_score:
            best_score = score
            best_row = row.to_dict()

    return best_row if best_score >= 0.6 else None


def _correct_with_dataset(raw_value: Any, candidates: list[Any], cutoff: float) -> Any:
    raw_text = str(raw_value or "").strip()
    if not raw_text or not candidates:
        return raw_value
    matches = get_close_matches(raw_text, [str(candidate) for candidate in candidates if str(candidate).strip()], n=1, cutoff=cutoff)
    return matches[0] if matches else raw_value


class Agent1ChequeValidator:
    """Agent 1: OCR extractor with dataset-backed correction."""

    def run(
        self,
        cheque_image_path: str,
        reference_record: Dict[str, Any],
        dataset_df: pd.DataFrame | None = None,
    ) -> Dict[str, Any]:
        image = cv2.imread(cheque_image_path)
        if image is None:
            return self._fail("Cheque image could not be read.")

        processed = _preprocess(image)
        raw_text = _ocr(processed)
        cleaned_text = _clean_ocr_text(raw_text)
        cleaned_lines = _clean_ocr_lines(raw_text)
        ocr_confidence = _ocr_confidence(processed)

        raw_extracted: Dict[str, Any] = {
            "payee_name": _extract_payee_name(cleaned_lines),
            "amount_digits": _extract_amount_digits(cleaned_text, cleaned_lines),
            "amount_words": _extract_amount_words(cleaned_lines),
            "date": _extract_date(cleaned_text),
            "cheque_number": _extract_cheque_number(cleaned_text),
            "bank_name": _extract_bank_name(cleaned_text),
            "account_number": reference_record.get("account_number", ""),
            "drawer_name": reference_record.get("drawer_name", ""),
            "ifsc": reference_record.get("ifsc", ""),
            "bank_branch": reference_record.get("bank_branch", ""),
            "payee_bank": reference_record.get("payee_bank", ""),
            "micr_code": reference_record.get("micr_code", ""),
        }
        extracted = dict(raw_extracted)
        matched_dataset_record = None

        if dataset_df is not None and not dataset_df.empty:
            matched_dataset_record = _select_dataset_record(raw_extracted, dataset_df)
            if matched_dataset_record:
                names = dataset_df["payee_name"].dropna().astype(str).tolist()
                amounts = dataset_df["amount_numbers"].dropna().astype(str).tolist()
                extracted["payee_name"] = matched_dataset_record.get("payee_name") or _correct_with_dataset(
                    raw_extracted.get("payee_name"),
                    names,
                    0.6,
                )
                corrected_amount = _correct_with_dataset(raw_extracted.get("amount_digits"), amounts, 0.5)
                extracted["amount_digits"] = float(matched_dataset_record.get("amount_numbers") or corrected_amount or 0)
                extracted["amount_words"] = matched_dataset_record.get("amount_words") or raw_extracted.get("amount_words")
                extracted["date"] = matched_dataset_record.get("date") or raw_extracted.get("date")
                extracted["cheque_number"] = matched_dataset_record.get("cheque_number") or raw_extracted.get("cheque_number")
                extracted["bank_name"] = matched_dataset_record.get("bank_name") or raw_extracted.get("bank_name")
                extracted["account_number"] = matched_dataset_record.get("account_number") or raw_extracted.get("account_number")
                extracted["ifsc"] = matched_dataset_record.get("ifsc_code") or raw_extracted.get("ifsc")

        missing_fields = [field for field in MANDATORY_FIELDS if extracted.get(field) in (None, "", 0, 0.0)]
        field_success_ratio = (len(MANDATORY_FIELDS) - len(missing_fields)) / len(MANDATORY_FIELDS)
        confidence = round(max(0.0, min(1.0, ocr_confidence * field_success_ratio)), 2)

        if len(missing_fields) == 0:
            status = "PASS"
        elif len(missing_fields) <= 2:
            status = "WARN"
        else:
            status = "FAIL"

        issues = [f"Missing OCR fields: {', '.join(missing_fields)}."] if missing_fields else []
        extracted["missing_fields"] = missing_fields

        return {
            "status": status,
            "confidence": confidence,
            "ocr_confidence": ocr_confidence,
            "raw_extracted": raw_extracted,
            "extracted": extracted,
            "corrected_values": {
                key: extracted.get(key)
                for key in ("payee_name", "amount_digits", "amount_words", "date", "cheque_number", "bank_name", "account_number", "ifsc")
            },
            "matched_dataset_record": matched_dataset_record,
            "missing_fields": missing_fields,
            "raw_text": cleaned_text,
            "ocr_text_preview": cleaned_text[:600],
            "issues": issues,
        }

    @staticmethod
    def _fail(reason: str) -> Dict[str, Any]:
        return {
            "status": "FAIL",
            "confidence": 0.0,
            "ocr_confidence": 0.0,
            "raw_extracted": {},
            "extracted": {},
            "corrected_values": {},
            "matched_dataset_record": None,
            "missing_fields": list(MANDATORY_FIELDS),
            "raw_text": "",
            "ocr_text_preview": "",
            "issues": [reason],
        }
