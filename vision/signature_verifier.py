from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

try:
    from skimage.metrics import structural_similarity as ssim
except ImportError:  # pragma: no cover - local fallback when scikit-image is absent
    ssim = None


def _fallback_ssim(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """
    Lightweight SSIM-style fallback so the demo still runs if scikit-image
    is not installed locally. Docker installs the real dependency.
    """
    image_a = image_a.astype(np.float64)
    image_b = image_b.astype(np.float64)

    c1 = 6.5025
    c2 = 58.5225

    mean_a = image_a.mean()
    mean_b = image_b.mean()
    var_a = image_a.var()
    var_b = image_b.var()
    cov = ((image_a - mean_a) * (image_b - mean_b)).mean()

    numerator = (2 * mean_a * mean_b + c1) * (2 * cov + c2)
    denominator = (mean_a**2 + mean_b**2 + c1) * (var_a + var_b + c2)
    return float(max(0.0, min(1.0, numerator / denominator)))


def _prepare_image(image_path: str | Path, size: tuple[int, int] = (220, 80)) -> np.ndarray:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    _, thresholded = cv2.threshold(image, 220, 255, cv2.THRESH_BINARY_INV)
    coords = cv2.findNonZero(thresholded)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        image = image[y:y + h, x:x + w]
    return cv2.resize(image, size)


def verify_signature(
    cheque_signature_path: str | Path,
    reference_signature_path: str | Path,
    threshold: float = 0.7,
) -> dict:
    cheque_signature = _prepare_image(cheque_signature_path)
    reference_signature = _prepare_image(reference_signature_path)

    if ssim is not None:
        ssim_score = float(ssim(cheque_signature, reference_signature))
    else:
        ssim_score = _fallback_ssim(cheque_signature, reference_signature)

    cheque_binary = cv2.threshold(cheque_signature, 220, 255, cv2.THRESH_BINARY_INV)[1]
    reference_binary = cv2.threshold(reference_signature, 220, 255, cv2.THRESH_BINARY_INV)[1]
    template_score = float(cv2.matchTemplate(cheque_binary, reference_binary, cv2.TM_CCOEFF_NORMED).max())
    similarity_score = max(ssim_score, template_score)

    return {
        "signature_score": similarity_score,
        "signature_valid": similarity_score > threshold,
        "threshold": threshold,
        "ssim_score": ssim_score,
        "template_score": template_score,
        "cheque_signature_path": str(cheque_signature_path),
        "reference_signature_path": str(reference_signature_path),
    }
