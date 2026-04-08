from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

CHEQUES_DIR = Path(__file__).resolve().parents[2] / "data" / "cheques"
EXTERNAL_CHEQUES_DIR = Path("e:/cheque")
TEMP_DIR = Path(__file__).resolve().parents[2] / "data" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Normalised size for SSIM comparison
NORM_W, NORM_H = 200, 100


def _to_binary(gray: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def _ink_pixel_ratio(binary: np.ndarray) -> float:
    """Fraction of dark (ink) pixels — 0 means blank, >0.02 likely a signature."""
    dark = np.sum(binary < 128)
    return dark / max(binary.size, 1)


def _normalize(gray: np.ndarray) -> np.ndarray:
    return cv2.resize(gray, (NORM_W, NORM_H))


class Agent2SignatureVerifier:
    """Agent 2: Compares cheque with its paired stored signature using SSIM."""

    PASS_THRESHOLD = 0.65
    WARN_THRESHOLD = 0.45

    def run(
        self,
        cheque_image_path: str,
        signature_paths: list[str] | None = None,
    ) -> Dict[str, Any]:
        # ── Load cheque ───────────────────────────────────────────────────────
        image = cv2.imread(cheque_image_path)
        if image is None:
            return self._fail("Cheque image could not be read.")

        h, w = image.shape[:2]

        # ── Crop bottom 30% height, right 50% width (signature region) ───────
        crop_bgr = image[int(h * 0.70):h, int(w * 0.50):w]
        crop_gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

        # Detect whether there's actual ink
        crop_norm = _normalize(crop_gray)
        signature_detected = _ink_pixel_ratio(_to_binary(crop_norm)) > 0.02

        # Save crop for UI display
        crop_save_path = str(TEMP_DIR / "cropped_signature.png")
        cv2.imwrite(crop_save_path, crop_bgr)

        # ── Find stored paired signature ──────────────────────────────────────
        stored_sig_path = self._find_stored_signature(cheque_image_path, signature_paths)

        if not stored_sig_path or not Path(stored_sig_path).exists():
            return {
                "status": "FAIL",
                "confidence": 0.0,
                "best_match_score": 0.0,
                "matched_signature": "",
                "matched_signature_path": "",
                "stored_signature_path": "",
                "cropped_path": crop_save_path,
                "signature_detected": signature_detected,
                "issues": ["No reference signature found"],
            }

        # ── Load and normalize reference signature ────────────────────────────
        ref_gray = cv2.imread(stored_sig_path, cv2.IMREAD_GRAYSCALE)
        if ref_gray is None:
            return self._fail("Stored reference signature could not be read.")

        ref_norm = _normalize(ref_gray)

        # ── SSIM comparison ───────────────────────────────────────────────────
        score, _ = ssim(crop_norm, ref_norm, full=True)
        score = float(score)

        # Also scan additional PDF signature_paths if provided
        best_score = score
        best_match = stored_sig_path

        if signature_paths:
            for sig_path in signature_paths:
                extra = cv2.imread(sig_path, cv2.IMREAD_GRAYSCALE)
                if extra is None:
                    continue
                extra_norm = _normalize(extra)
                s, _ = ssim(crop_norm, extra_norm, full=True)
                if float(s) > best_score:
                    best_score = float(s)
                    best_match = sig_path

        # ── Decision ─────────────────────────────────────────────────────────
        issues: list[str] = []
        if best_score >= self.PASS_THRESHOLD:
            status = "PASS"
        elif best_score >= self.WARN_THRESHOLD or signature_detected:
            # Signature is present but low match → WARN, not FAIL
            status = "WARN"
            issues.append(f"Signature detected but match score is borderline ({best_score:.2f}).")
        else:
            status = "FAIL"
            issues.append(f"Signature mismatch (score: {best_score:.2f}, threshold: {self.PASS_THRESHOLD}).")

        return {
            "status": status,
            "confidence": round(max(0.0, best_score), 2),
            "best_match_score": round(best_score, 3),
            "matched_signature": Path(best_match).name if best_match else "",
            "matched_signature_path": best_match,
            "stored_signature_path": stored_sig_path,
            "cropped_path": crop_save_path,
            "signature_detected": signature_detected,
            "issues": issues,
        }

    def _find_stored_signature(
        self,
        cheque_image_path: str,
        extra_signature_paths: list[str] | None,
    ) -> str | None:
        stem = Path(cheque_image_path).stem
        search_dirs = [
            Path(cheque_image_path).parent,
            CHEQUES_DIR,
            EXTERNAL_CHEQUES_DIR,
        ]
        for directory in search_dirs:
            for ext in (".png", ".jpg", ".jpeg"):
                candidate = directory / f"{stem}_signature{ext}"
                if candidate.exists():
                    return str(candidate)
        return None

    @staticmethod
    def _fail(reason: str) -> Dict[str, Any]:
        return {
            "status": "FAIL",
            "confidence": 0.0,
            "best_match_score": 0.0,
            "matched_signature": "",
            "matched_signature_path": "",
            "stored_signature_path": "",
            "cropped_path": "",
            "signature_detected": False,
            "issues": [reason],
        }
