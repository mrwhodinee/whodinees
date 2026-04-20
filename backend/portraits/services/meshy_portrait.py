"""Meshy image-to-3D API helper for pet portraits.

Docs: https://docs.meshy.ai/api/image-to-3d
Endpoint: POST /openapi/v1/image-to-3d  (v1 is the stable image-to-3d route)
"""
from __future__ import annotations
import base64
import logging
import mimetypes
import time
from typing import Tuple
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MESHY_BASE = "https://api.meshy.ai"
IMAGE_TO_3D_URL = f"{MESHY_BASE}/openapi/v1/image-to-3d"


def _headers() -> dict:
    key = settings.MESHY_API_KEY
    if not key:
        raise RuntimeError("MESHY_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _image_to_data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def submit_portrait_task(image_path: str, seed: int | None = None) -> str:
    """Kick off an image-to-3d task. Returns Meshy task_id.

    Uses meshy-6 topology, 30k polycount, remesh on, no PBR (figurine-grade).
    """
    data_uri = _image_to_data_uri(image_path)
    payload = {
        "image_url": data_uri,
        "ai_model": "meshy-6",
        "topology": "triangle",
        "target_polycount": 30000,
        "should_remesh": True,
        "should_texture": True,
        "enable_pbr": False,
        "symmetry_mode": "auto",
    }
    if seed is not None:
        payload["seed"] = seed

    resp = requests.post(IMAGE_TO_3D_URL, json=payload, headers=_headers(), timeout=90)
    if resp.status_code >= 400:
        logger.error("Meshy image-to-3d create failed %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    data = resp.json()
    return data.get("result") or data.get("id") or data.get("task_id") or ""


def submit_variants(image_path: str, n: int = 3) -> list[str]:
    """Submit N portrait tasks with seed variation. Returns list of task_ids."""
    task_ids: list[str] = []
    for i in range(n):
        try:
            # Seed variation gives diverse results from the same image.
            tid = submit_portrait_task(image_path, seed=1000 + i * 101)
            if tid:
                task_ids.append(tid)
        except Exception as e:
            logger.exception("Failed to submit variant %d: %s", i, e)
    return task_ids


def get_task(task_id: str) -> dict:
    resp = requests.get(
        f"{IMAGE_TO_3D_URL}/{task_id}",
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code >= 400:
        logger.error("Meshy get failed %s: %s", resp.status_code, resp.text[:300])
        resp.raise_for_status()
    return resp.json()


def poll_task(task_id: str) -> dict:
    """One-shot poll; returns normalized dict.
    { task_id, status, progress, preview_url, glb_url, fbx_url, usdz_url }
    """
    task = get_task(task_id)
    status = (task.get("status") or "").upper()
    model_urls = task.get("model_urls") or {}
    return {
        "task_id": task_id,
        "status": status,
        "progress": task.get("progress", 0),
        "preview_url": task.get("thumbnail_url") or task.get("video_url") or "",
        "glb_url": model_urls.get("glb") or "",
        "fbx_url": model_urls.get("fbx") or "",
        "usdz_url": model_urls.get("usdz") or "",
        "raw": task,
    }


def poll_until_done(task_id: str, timeout_s: int = 600, interval_s: int = 10) -> dict:
    start = time.time()
    while True:
        task = get_task(task_id)
        status = (task.get("status") or "").upper()
        if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
            return task
        if status in ("FAILED", "CANCELED", "EXPIRED", "ERROR"):
            raise RuntimeError(f"Meshy task {task_id} failed: {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Meshy task {task_id} timed out (last status={status})")
        time.sleep(interval_s)


def download_preview_and_glb(task_id: str) -> Tuple[bytes | None, str]:
    """Returns (preview_png_bytes_or_None, glb_url)."""
    task = get_task(task_id)
    preview_bytes = None
    thumb_url = task.get("thumbnail_url") or ""
    if thumb_url:
        try:
            r = requests.get(thumb_url, timeout=60)
            if r.status_code < 400:
                preview_bytes = r.content
        except Exception as e:
            logger.warning("Thumb download failed: %s", e)
    glb_url = (task.get("model_urls") or {}).get("glb") or ""
    return preview_bytes, glb_url
