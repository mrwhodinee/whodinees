"""Meshy text-to-3D API helper.

Docs: https://docs.meshy.ai/
We use the Text-to-3D v2 endpoint: POST /openapi/v2/text-to-3d
The "preview" stage returns a thumbnail_url/video_url and a model_urls.* file.
"""
import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MESHY_BASE = "https://api.meshy.ai"


def _headers() -> dict:
    key = settings.MESHY_API_KEY
    if not key:
        raise RuntimeError("MESHY_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def create_text_to_3d_preview(prompt: str, art_style: str = "realistic") -> str:
    """Kick off a preview task; returns the Meshy task id."""
    resp = requests.post(
        f"{MESHY_BASE}/openapi/v2/text-to-3d",
        json={
            "mode": "preview",
            "prompt": prompt,
            "art_style": art_style,
            "negative_prompt": "low quality, blurry, ugly, deformed",
        },
        headers=_headers(),
        timeout=60,
    )
    if resp.status_code >= 400:
        logger.error("Meshy create failed %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    data = resp.json()
    # v2 may return {"result": "<id>"} or {"id": "<id>"}
    return data.get("result") or data.get("id") or data.get("task_id")


def get_task(task_id: str) -> dict:
    resp = requests.get(
        f"{MESHY_BASE}/openapi/v2/text-to-3d/{task_id}",
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code >= 400:
        logger.error("Meshy get failed %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    return resp.json()


def poll_until_done(task_id: str, timeout_s: int = 600, interval_s: int = 8) -> dict:
    start = time.time()
    while True:
        task = get_task(task_id)
        status = (task.get("status") or "").upper()
        if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
            return task
        if status in ("FAILED", "CANCELED", "EXPIRED", "ERROR"):
            raise RuntimeError(f"Meshy task {task_id} ended in status {status}: {task}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Meshy task {task_id} did not complete within {timeout_s}s (last status={status})")
        time.sleep(interval_s)


def download_thumbnail(task: dict, dest_path: str) -> bool:
    """Download the preview thumbnail PNG to dest_path. Returns True on success."""
    url = task.get("thumbnail_url") or ""
    if not url:
        # Some responses use video_url only; try rendered_image_urls or similar
        renders = task.get("rendered_image_urls") or {}
        if isinstance(renders, dict):
            url = renders.get("front") or next(iter(renders.values()), "")
    if not url:
        logger.warning("Meshy task %s: no thumbnail_url available", task.get("id"))
        return False
    r = requests.get(url, timeout=60, stream=True)
    if r.status_code >= 400:
        logger.error("Thumbnail download failed %s: %s", r.status_code, url)
        return False
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return True
