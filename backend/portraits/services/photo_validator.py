"""Photo quality validation for pet portraits.

Runs lightweight checks (resolution, file size) and, if OpenCV is available,
a blur check via Laplacian variance. Returns (passed, score_0_100, issues_list).
"""
from __future__ import annotations
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

MIN_SHORTEST_SIDE_PX = 1400  # Raised for premium quality
MAX_FILE_BYTES = 15 * 1024 * 1024
MIN_FILE_BYTES = 100 * 1024  # 100KB minimum
MIN_ACCEPTABLE_SCORE = 80  # 8/10 quality gate


def validate_photo(file_path: str) -> Tuple[bool, int, List[str]]:
    """Validate a photo on disk. Returns (passed, score, issues)."""
    issues: List[str] = []
    score = 100

    try:
        import os
        size = os.path.getsize(file_path)
    except OSError as e:
        return False, 0, [f"Could not read file: {e}"]

    if size < MIN_FILE_BYTES:
        issues.append(f"File is too small ({size // 1024}KB); we need a high-resolution photo (minimum 100KB).")
        score -= 50
    elif size > MAX_FILE_BYTES:
        issues.append(f"File is too large ({size // 1024 // 1024}MB); max is 15MB.")
        score -= 30

    # Resolution check (Pillow is already required)
    try:
        from PIL import Image
        with Image.open(file_path) as im:
            w, h = im.size
            short = min(w, h)
            if short < MIN_SHORTEST_SIDE_PX:
                issues.append(
                    f"Image resolution too low ({w}×{h}). We need at least {MIN_SHORTEST_SIDE_PX}px on the shortest side for premium quality."
                )
                score -= 50
            elif short < 1800:
                score -= 15  # below ideal but passable
    except Exception as e:
        issues.append(f"Could not read image: {e}")
        score = 0
        return False, score, issues

    # Optional blur check via OpenCV Laplacian variance
    try:
        import cv2  # type: ignore
        import numpy as np  # noqa: F401
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            lap_var = cv2.Laplacian(img, cv2.CV_64F).var()
            # Strict blur threshold for premium service
            # Typical: > 500 = sharp, 100-500 = usable, < 100 = blurry
            if lap_var < 100:
                issues.append("Photo is too blurry. Please upload a sharp, well-focused image.")
                score -= 40
            elif lap_var < 200:
                issues.append("Photo could be sharper for best results.")
                score -= 20
    except ImportError:
        # OpenCV not installed — skip blur check.
        # TODO: add opencv-python-headless to requirements if we want this live.
        logger.debug("cv2 not available; skipping blur check")
    except Exception as e:
        logger.warning("Blur check failed: %s", e)

    # TODO: single-subject check (e.g. MediaPipe or a small ONNX model) — not
    # implemented. For now we rely on the customer and a manual review step.

    score = max(0, min(100, score))
    # Premium service: require 80+ score (8/10)
    passed = score >= MIN_ACCEPTABLE_SCORE and not any(
        phrase in i.lower() for i in issues 
        for phrase in ["too small", "too large", "too low", "too blurry"]
    )
    return passed, score, issues
