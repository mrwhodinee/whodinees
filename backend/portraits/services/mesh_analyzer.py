"""Mesh analysis utilities using trimesh."""
from __future__ import annotations
import logging
import trimesh
import tempfile
import requests

logger = logging.getLogger(__name__)


def analyze_glb(glb_url_or_path: str) -> dict:
    """Analyze a GLB file and return volume, polycount, etc.
    
    Args:
        glb_url_or_path: URL or local file path to GLB
    
    Returns:
        {
            "volume_cm3": 0.85,
            "polycount": 25000,
            "bbox_mm": [40, 35, 50],
            "is_watertight": True,
        }
    """
    try:
        # Download if URL
        if glb_url_or_path.startswith("http"):
            resp = requests.get(glb_url_or_path, timeout=60)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
                f.write(resp.content)
                path = f.name
        else:
            path = glb_url_or_path
        
        # Load mesh
        mesh = trimesh.load(path, force="mesh")
        
        # If it's a Scene with multiple meshes, combine them
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=m.vertices, faces=m.faces)
                      for m in mesh.geometry.values())
            )
        
        # Calculate properties
        # Volume: trimesh gives cubic mm if units are mm, but Meshy outputs are
        # typically in arbitrary units. We'll assume the model is scaled to real-world
        # size (e.g., 40mm figurine = 40 units). Volume is in cubic units, convert to cm³.
        # Note: Meshy's default scale is often 1 unit = 1mm.
        volume_cubic_mm = abs(mesh.volume)
        volume_cm3 = volume_cubic_mm / 1000.0  # 1 cm³ = 1000 mm³
        
        # Bounding box in mm
        bbox = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        bbox_size = bbox[1] - bbox[0]
        
        # Polycount
        polycount = len(mesh.faces)
        
        # Watertight check
        is_watertight = mesh.is_watertight
        
        return {
            "volume_cm3": round(volume_cm3, 2),
            "polycount": polycount,
            "bbox_mm": [round(x, 1) for x in bbox_size],
            "is_watertight": is_watertight,
        }
        
    except Exception as e:
        logger.exception("Failed to analyze mesh: %s", e)
        return {
            "volume_cm3": 0.85,  # fallback estimate for ~40mm figurine
            "polycount": 20000,
            "bbox_mm": [40, 35, 50],
            "is_watertight": False,
            "error": str(e),
        }
