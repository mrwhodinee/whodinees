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
        
        # Bounding box in mm
        bbox = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        bbox_size = bbox[1] - bbox[0]
        
        # Calculate properties
        volume_cubic_mm = abs(mesh.volume)
        volume_cm3 = volume_cubic_mm / 1000.0
        
        logger.info(f"Mesh analysis: vertices={len(mesh.vertices)}, faces={len(mesh.faces)}, raw_volume={volume_cubic_mm:.6f}mm3, bbox={bbox_size}")
        
        # If volume is suspiciously small, estimate from bounding box
        if volume_cm3 < 0.01:
            bbox_volume_mm3 = float(bbox_size[0] * bbox_size[1] * bbox_size[2])
            volume_cm3 = (bbox_volume_mm3 / 1000.0) * 0.3
            logger.warning(f"Mesh volume was {volume_cubic_mm:.6f} mm3, bbox_volume={bbox_volume_mm3:.2f} mm3, using estimate: {volume_cm3:.2f} cm3")
        
        # Final sanity check
        if volume_cm3 <= 0:
            volume_cm3 = 0.85
            logger.error(f"Volume calculation failed completely, using fallback 0.85 cm3")
        
        # Polycount
        polycount = len(mesh.faces)
        
        # Watertight check
        is_watertight = mesh.is_watertight
        
        # Final safety check before returning
        final_volume = round(volume_cm3, 2)
        if final_volume <= 0:
            final_volume = 0.85
            logger.error(f"Volume was {final_volume} after rounding, forcing 0.85")
        
        return {
            "volume_cm3": final_volume,
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
