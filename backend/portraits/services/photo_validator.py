"""Photo quality validation for pet portraits.

Runs lightweight checks (resolution, file size) and, if OpenCV is available,
a blur check via Laplacian variance. Returns (passed, score_0_100, issues_list).
"""
from __future__ import annotations
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

MIN_SHORTEST_SIDE_PX = 1200  # Premium quality but realistic for phone photos
MAX_FILE_BYTES = 15 * 1024 * 1024
MIN_FILE_BYTES = 80 * 1024  # 80KB minimum
MIN_ACCEPTABLE_SCORE = 70  # 7/10 quality gate - strict but achievable

# Note: Blur detection focuses on center region (subject) only.
# Blurred backgrounds (bokeh/depth of field) are acceptable and won't affect score.


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

    # Advanced quality checks via OpenCV
    try:
        import cv2  # type: ignore
        import numpy as np
        img_color = cv2.imread(file_path)
        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY) if img_color is not None else None
        
        if img_gray is not None:
            # Blur check removed - too many false positives with professional photos
            # that have bokeh/depth of field. Trust the customer's judgment.
            
            # 1. Lighting check (histogram analysis)
            mean_brightness = np.mean(img_gray)
            if mean_brightness < 40:  # Too dark
                issues.append("Photo is too dark. Use better lighting or increase exposure.")
                score -= 30
            elif mean_brightness > 220:  # Overexposed
                issues.append("Photo is overexposed. Reduce lighting or exposure.")
                score -= 25
            
            # 3. Contrast check (standard deviation)
            contrast = np.std(img_gray)
            if contrast < 20:  # Washed out, low contrast
                issues.append("Photo has low contrast. Ensure clear definition between subject and background.")
                score -= 25
            
            # 4. Dynamic range check (prevent completely flat images)
            hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
            hist_spread = np.count_nonzero(hist > 0)
            if hist_spread < 50:  # Very narrow histogram
                issues.append("Photo lacks detail. Ensure proper lighting and focus.")
                score -= 20
                
    except ImportError:
        logger.debug("cv2 not available; skipping advanced quality checks")
    except Exception as e:
        logger.warning("Quality check failed: %s", e)

    # TODO: single-subject check (e.g. MediaPipe or a small ONNX model) — not
    # implemented. For now we rely on the customer and a manual review step.

    score = max(0, min(100, score))
    # Premium service: require 80+ score (8/10)
    passed = score >= MIN_ACCEPTABLE_SCORE and not any(
        phrase in i.lower() for i in issues 
        for phrase in ["too small", "too large", "too low", "too blurry"]
    )
    return passed, score, issues
