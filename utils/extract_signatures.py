from __future__ import annotations

from pathlib import Path
from time import time_ns

import cv2
import fitz
import numpy as np


def _segment_signatures(image: np.ndarray) -> list[np.ndarray]:
    if image is None:
        return []

    _, thresholded = cv2.threshold(image, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    segments: list[np.ndarray] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < 800 or w < 40 or h < 15:
            continue
        crop = image[max(0, y - 5): y + h + 5, max(0, x - 5): x + w + 5]
        segments.append(crop)

    segments.sort(key=lambda segment: segment.shape[1] * segment.shape[0], reverse=True)
    return segments


def extract_signatures_from_pdf(pdf_path: str, output_dir: str) -> list[str]:
    """
    Extract all embedded images from a signature PDF and save them as PNG files.
    """
    pdf = fitz.open(pdf_path)
    root_output = Path(output_dir)
    run_output = root_output / f"extract_{time_ns()}"
    run_output.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []
    image_counter = 1

    for page in pdf:
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            base_image = pdf.extract_image(xref)
            image_bytes = base_image["image"]
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            decoded = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
            if decoded is None:
                pix = fitz.Pixmap(pdf, xref)
                matrix = np.frombuffer(pix.tobytes("png"), dtype=np.uint8)
                decoded = cv2.imdecode(matrix, cv2.IMREAD_GRAYSCALE)
                pix = None

            segments = _segment_signatures(decoded)
            if segments:
                for segment in segments:
                    segmented_path = run_output / f"sig_{image_counter:03d}.png"
                    cv2.imwrite(str(segmented_path), segment)
                    saved_paths.append(str(segmented_path))
                    image_counter += 1
            else:
                file_path = run_output / f"sig_{image_counter:03d}.png"
                cv2.imwrite(str(file_path), decoded)
                saved_paths.append(str(file_path))
                image_counter += 1

    pdf.close()
    return saved_paths
