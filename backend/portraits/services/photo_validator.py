"""Photo quality validation for pet portraits.

Runs lightweight checks (resolution, file size) and, if OpenCV is available,
a blur check via Laplacian variance. Returns (passed, score_0_100, issues_list).
"""
from __future__ import annotations
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

MIN_SHORTEST_SIDE_PX = 1024
MAX_FILE_BYTES = 15 * 1024 * 1024
MIN_FILE_BYTES = 50 * 1024  # 50KB — below this we assume junk


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
        issues.append(f"File is too small ({size} bytes); please upload a higher-quality photo.")
        score -= 40
    elif size > MAX_FILE_BYTES:
        issues.append(f"File is too large ({size} bytes); max is {MAX_FILE_BYTES} bytes.")
        score -= 30

    # Resolution check (Pillow is already required)
    try:
        from PIL import Image
        with Image.open(file_path) as im:
            w, h = im.size
            short = min(w, h)
            if short < MIN_SHORTEST_SIDE_PX:
                issues.append(
                    f"Image is too small ({w}×{h}); we need at least {MIN_SHORTEST_SIDE_PX}px on the shortest side."
                )
                score -= 40
            elif short < 1400:
                score -= 10  # acceptable but not great
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
            # Typical: > 500 = sharp, 100-500 = usable, < 100 = blurry
            if lap_var < 60:
                issues.append("Photo appears blurry; a sharper photo will produce a much better portrait.")
                score -= 30
            elif lap_var < 150:
                score -= 10
    except ImportError:
        # OpenCV not installed — skip blur check.
        # TODO: add opencv-python-headless to requirements if we want this live.
        logger.debug("cv2 not available; skipping blur check")
    except Exception as e:
        logger.warning("Blur check failed: %s", e)

    # TODO: single-subject check (e.g. MediaPipe or a small ONNX model) — not
    # implemented. For now we rely on the customer and a manual review step.

    score = max(0, min(100, score))
    passed = score >= 60 and not any("too small" in i.lower() or "too large" in i.lower() for i in issues)
    return passed, score, issues
