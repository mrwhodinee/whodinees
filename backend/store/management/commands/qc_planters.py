"""
Download and QC the meshes for every Product with a meshy_task_id.

Usage:
    python manage.py qc_planters [--only ID1,ID2] [--redownload] [--no-persist]

Mesh files and JSON reports are written to /tmp/whodinees-meshes/ by default
(outside the repo) so they never end up in git. Override with --mesh-dir.

Produces:
    - <mesh-dir>/<product_slug>.glb       (downloaded mesh)
    - <mesh-dir>/per_product/<id>.json    (per-product detail)
    - <mesh-dir>/qc_report.json           (aggregate report)

Also writes QC results onto Product (volume_cm3, is_functional_planter, qc_notes)
unless --no-persist is given.

Heuristics for "is this a functional planter?":
    is_watertight OR (hollow_ratio >= 0.3 AND has_drainage AND fits_3_4_pot)
Additional diagnostics:
    - open interior cavity near the top (upward-facing concavity of sufficient size)
    - drainage hole at the bottom (ray from below the base passes up into an interior void)
    - interior can hold a 3–4" nursery pot (>=80mm diameter, >=70mm depth)
    - stable flat-ish base
"""
import json
import logging
import os
from pathlib import Path

import numpy as np
import requests
import trimesh
from django.conf import settings
from django.core.management.base import BaseCommand

from store.models import Product
from store.services import meshy

logger = logging.getLogger(__name__)

# Normalize every mesh to physical units (mm).
# Meshy returns models in arbitrary units; we scale so the longest bounding-box
# edge is ~100mm (target finished planter size).
TARGET_LONGEST_EDGE_MM = 100.0

POT_MIN_DIAM_MM = 80.0
POT_MIN_DEPTH_MM = 70.0
MIN_WALL_MM = 1.5
DRAIN_MAX_DIAM_MM = 20.0


def _download(url: str, dest: Path) -> None:
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 15):
            f.write(chunk)


def _load_mesh(path: Path) -> trimesh.Trimesh:
    """Load a GLB/OBJ/STL and return a single concatenated Trimesh in mm."""
    scene_or_mesh = trimesh.load(str(path), force="mesh")
    if isinstance(scene_or_mesh, trimesh.Scene):
        # Shouldn't happen with force='mesh' but just in case.
        geom = trimesh.util.concatenate(
            [g for g in scene_or_mesh.geometry.values()]
        )
    else:
        geom = scene_or_mesh
    if not isinstance(geom, trimesh.Trimesh) or geom.is_empty:
        raise ValueError(f"Empty or non-triangle mesh: {path}")

    # Orient so "up" is +Z. Meshy glb models are typically Y-up. Rotate -90° about X.
    # Heuristic: the longest "width" axis should be XY, and Z should be height.
    # If extents suggest Y is the tallest axis, swap Y/Z.
    ext = geom.extents  # [x, y, z]
    if ext[1] > ext[0] and ext[1] > ext[2]:
        # Y is tallest — rotate so Y→Z (up)
        R = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        geom.apply_transform(R)

    # Scale so longest edge = TARGET_LONGEST_EDGE_MM (mm).
    longest = float(max(geom.extents))
    if longest > 0:
        geom.apply_scale(TARGET_LONGEST_EDGE_MM / longest)

    # Translate so min Z == 0 (sit on the floor).
    tmin = geom.bounds[0]
    geom.apply_translation([-tmin[0] - (geom.extents[0] / 2),
                             -tmin[1] - (geom.extents[1] / 2),
                             -tmin[2]])
    return geom


def _ray_cast_from_above(mesh: trimesh.Trimesh, xy: np.ndarray) -> np.ndarray:
    """Return Z-intersections, sorted descending (top first), of vertical rays at xy (N,2)."""
    origins = np.c_[xy, np.full(len(xy), mesh.bounds[1, 2] + 10.0)]
    directions = np.tile([0, 0, -1.0], (len(xy), 1))
    locs, ray_idx, _ = mesh.ray.intersects_location(
        ray_origins=origins, ray_directions=directions, multiple_hits=True
    )
    # group by ray
    out = [[] for _ in range(len(xy))]
    for loc, ri in zip(locs, ray_idx):
        out[ri].append(loc[2])
    for l in out:
        l.sort(reverse=True)
    return out


def _interior_analysis(mesh: trimesh.Trimesh) -> dict:
    """Raycast grid from above to find the interior cavity profile."""
    ext = mesh.extents
    cx = (mesh.bounds[0, 0] + mesh.bounds[1, 0]) / 2
    cy = (mesh.bounds[0, 1] + mesh.bounds[1, 1]) / 2

    # Grid across inner 70% of the footprint (avoids wall slivers).
    n = 25
    half_x = ext[0] * 0.45
    half_y = ext[1] * 0.45
    xs = np.linspace(cx - half_x, cx + half_x, n)
    ys = np.linspace(cy - half_y, cy + half_y, n)
    XY = np.array([[x, y] for x in xs for y in ys])

    hits = _ray_cast_from_above(mesh, XY)

    # For each ray, determine if there's an interior void (top entering wall + bottom wall beneath it),
    # i.e. >=2 intersections with a gap between them.
    interior_depth = np.full(len(XY), 0.0)
    top_of_cavity = np.full(len(XY), np.nan)
    bottom_of_cavity = np.full(len(XY), np.nan)
    open_top = np.zeros(len(XY), dtype=bool)

    mesh_top = mesh.bounds[1, 2]
    for i, zs in enumerate(hits):
        if len(zs) >= 2:
            # zs sorted descending: [top_outer, inner_ceiling, ...] — typical planter has 2 hits
            # (enter outer wall top) and (hit inner floor). For a bowl with open top, ray enters
            # at outer rim and next hit is the bottom floor inside.
            z_top = zs[0]
            z_bot = zs[-1]  # inside floor (last hit above the bottom of the mesh)
            depth = z_top - z_bot
            if depth > 1.0:
                interior_depth[i] = depth
                top_of_cavity[i] = z_top
                bottom_of_cavity[i] = z_bot
                # "open top" if the topmost hit is within 3mm of mesh top (i.e. the ray barely
                # grazes the rim edge) — meaning overhead is clear above that opening.
                if (mesh_top - z_top) < 3.0:
                    open_top[i] = True
        elif len(zs) == 1:
            # Single hit means the ray goes straight to the outer surface only — could be either
            # solid blob OR an open interior where ray re-enters at this same point. If the hit is
            # near the mesh top, probably open sky (rim). Not counted as cavity.
            pass

    # Did we find any substantial interior?
    depths_in_cavity = interior_depth[interior_depth > 1.0]
    if len(depths_in_cavity) == 0:
        return {
            "has_cavity": False,
            "interior_depth_mm": 0.0,
            "interior_diameter_mm": 0.0,
            "cavity_points": 0,
            "grid_n": int(len(XY)),
        }

    # Cavity "diameter" — grid resolution × fraction of grid with deep cavity.
    cav_mask = interior_depth >= max(15.0, POT_MIN_DEPTH_MM * 0.5)
    if not cav_mask.any():
        cav_mask = interior_depth > 1.0
    cav_pts = XY[cav_mask]
    if len(cav_pts) >= 3:
        # diameter = 2 * max radial distance from centroid
        c = cav_pts.mean(axis=0)
        rmax = float(np.linalg.norm(cav_pts - c, axis=1).max())
        diameter = 2.0 * rmax
    else:
        diameter = 0.0

    return {
        "has_cavity": True,
        "interior_depth_mm": float(depths_in_cavity.max()),
        "interior_diameter_mm": float(diameter),
        "cavity_points": int(cav_mask.sum()),
        "grid_n": int(len(XY)),
    }


def _drainage_check(mesh: trimesh.Trimesh, cavity_info: dict) -> dict:
    """Ray from below the center — does it enter an interior void?
    Classic planter signature: ray from below hits the bottom wall, then the inner floor, then the top opening (or nothing if bowl is open).
    If there's a hole in the base, the ray travels straight into the cavity, producing fewer/different hits.
    """
    cx = (mesh.bounds[0, 0] + mesh.bounds[1, 0]) / 2
    cy = (mesh.bounds[0, 1] + mesh.bounds[1, 1]) / 2

    # small ring of rays near the base center (radius 0..5mm) — covers off-center drain holes
    ring_radii = [0.0, 2.0, 4.0, 6.0, 8.0]
    n_ring = 12
    drain_hits = 0
    total_rays = 0
    example_counts = []
    for r in ring_radii:
        if r == 0:
            pts = np.array([[cx, cy]])
        else:
            angles = np.linspace(0, 2 * np.pi, n_ring, endpoint=False)
            pts = np.c_[cx + r * np.cos(angles), cy + r * np.sin(angles)]

        origins = np.c_[pts, np.full(len(pts), mesh.bounds[0, 2] - 10.0)]
        directions = np.tile([0, 0, 1.0], (len(pts), 1))
        locs, ray_idx, _ = mesh.ray.intersects_location(
            ray_origins=origins, ray_directions=directions, multiple_hits=True
        )
        rays = [[] for _ in range(len(pts))]
        for loc, ri in zip(locs, ray_idx):
            rays[ri].append(loc[2])
        for rr in rays:
            total_rays += 1
            rr.sort()
            example_counts.append(len(rr))
            # A solid base has >=2 hits clustered near z=0 (enter bottom face, exit top of base thickness).
            # An open drain hole: the ray travels up into the cavity — we should see either 0-1 hits
            # clustered very low, OR the very first hit is already inside the cavity (z > some threshold).
            if len(rr) == 0:
                drain_hits += 1  # went all the way through
            elif len(rr) == 1:
                # only one hit — ray exited somewhere and came back to sky. ambiguous, skip.
                pass
            else:
                # Look for a big gap between first and second hit — that gap is the interior cavity.
                gaps = np.diff(rr)
                if gaps.max() >= 5.0 and rr[0] < 10.0:
                    # first hit near base, then a gap >= 5mm ⇒ cavity above a thin base. That means
                    # a closed base (no drain). So drain only counted when either 0 hits OR the first
                    # hit is much higher than the base (the ray reached the cavity without hitting
                    # any base material).
                    pass
                if rr[0] > 5.0:
                    # first hit is well above the base — probably an empty hole at the base
                    drain_hits += 1

    has_drain = drain_hits >= 1 and cavity_info.get("has_cavity", False)
    return {
        "has_drain": bool(has_drain),
        "drain_ray_hits": int(drain_hits),
        "total_rays": int(total_rays),
        "sample_hit_counts": example_counts[:10],
    }


def _base_flatness(mesh: trimesh.Trimesh) -> dict:
    """How flat is the bottom? Look at faces whose centroid-Z is in the lowest 5% and whose
    normal points roughly downward; measure their XY-projected area."""
    z_low = mesh.bounds[0, 2]
    z_thresh = z_low + max(3.0, 0.05 * mesh.extents[2])

    face_centroids = mesh.triangles_center
    face_normals = mesh.face_normals
    face_areas = mesh.area_faces

    low_mask = face_centroids[:, 2] <= z_thresh
    # downward-pointing normals
    down_mask = face_normals[:, 2] < -0.5
    mask = low_mask & down_mask

    base_area = float(face_areas[mask].sum())
    footprint_area = float(mesh.extents[0] * mesh.extents[1])
    ratio = base_area / footprint_area if footprint_area > 0 else 0.0
    return {
        "base_area_mm2": base_area,
        "footprint_area_mm2": footprint_area,
        "base_to_footprint_ratio": float(ratio),
        "is_stable": bool(ratio >= 0.15),
    }


def qc_one(mesh_path: Path) -> dict:
    mesh = _load_mesh(mesh_path)

    report = {
        "mesh_file": str(mesh_path.name),
        "bbox_mm": [float(x) for x in mesh.extents],
        "volume_mm3": float(mesh.volume) if mesh.is_volume else None,
        "is_watertight": bool(mesh.is_watertight),
        "n_faces": int(len(mesh.faces)),
        "n_vertices": int(len(mesh.vertices)),
    }

    cav = _interior_analysis(mesh)
    report["cavity"] = cav

    drain = _drainage_check(mesh, cav)
    report["drainage"] = drain

    base = _base_flatness(mesh)
    report["base"] = base

    # Pass criteria (all must hold):
    fits_pot = (
        cav["has_cavity"]
        and cav["interior_diameter_mm"] >= POT_MIN_DIAM_MM
        and cav["interior_depth_mm"] >= POT_MIN_DEPTH_MM
    )
    report["checks"] = {
        "has_cavity":      cav["has_cavity"],
        "fits_3_4_pot":    bool(fits_pot),
        "has_drain":       drain["has_drain"],
        "stable_base":     base["is_stable"],
    }
    failures = [k for k, v in report["checks"].items() if not v]
    report["pass"] = len(failures) == 0
    report["failures"] = failures
    return report


class Command(BaseCommand):
    help = "Download meshes for every Product.meshy_task_id and QC them as planters."

    def add_arguments(self, parser):
        parser.add_argument("--only", type=str, default="", help="Comma-separated product IDs")
        parser.add_argument("--redownload", action="store_true")
        parser.add_argument(
            "--mesh-dir", type=str, default="/tmp/whodinees-meshes",
            help="Dir for downloaded meshes + reports (kept OUTSIDE the repo).",
        )
        parser.add_argument(
            "--no-persist", action="store_true",
            help="Do not write QC results back to Product rows.",
        )

    def handle(self, *args, **opts):
        mesh_dir = Path(opts["mesh_dir"]).resolve()
        report_dir = mesh_dir / "per_product"
        summary_path = mesh_dir / "qc_report.json"
        mesh_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)

        # Hard guard: never allow mesh dir inside the repo.
        repo_root = Path(settings.BASE_DIR).resolve().parent
        try:
            mesh_dir.relative_to(repo_root)
            raise RuntimeError(
                f"Refusing to write meshes inside repo tree ({mesh_dir}). "
                f"Use --mesh-dir with a path outside {repo_root}."
            )
        except ValueError:
            pass  # not inside repo — good.

        only_ids = set()
        if opts["only"]:
            only_ids = {int(x) for x in opts["only"].split(",") if x.strip()}

        products = Product.objects.exclude(meshy_task_id="").order_by("id")
        if only_ids:
            products = products.filter(id__in=only_ids)

        all_reports = []
        for p in products:
            self.stdout.write(f"\n▶ #{p.id} {p.name} (task {p.meshy_task_id})")
            # Prefer slug-named file; keep backwards-compat with id-named.
            mesh_path = mesh_dir / f"{p.slug or p.id}.glb"
            legacy_path = mesh_dir / f"{p.id}.glb"
            if not mesh_path.exists() and legacy_path.exists():
                mesh_path = legacy_path

            try:
                if not mesh_path.exists() or opts["redownload"]:
                    task = meshy.get_task(p.meshy_task_id)
                    urls = task.get("model_urls") or {}
                    url = urls.get("glb") or urls.get("obj") or urls.get("stl")
                    if not url:
                        raise RuntimeError("no model_urls in task")
                    self.stdout.write(f"   downloading → {mesh_path.name}")
                    _download(url, mesh_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   download failed: {e}"))
                all_reports.append({"product_id": p.id, "name": p.name, "error": str(e)})
                continue

            try:
                rep = qc_one(mesh_path)
                rep["product_id"] = p.id
                rep["name"] = p.name
                rep["slug"] = p.slug
                rep["category_current"] = p.category_id
                rep["price_current"] = str(p.price)

                # Derived: hollow_ratio, volume_cm3, planter_fitness_score,
                # functional-planter verdict (watertight OR hollow+drain+fit).
                bbox_mm = rep["bbox_mm"]
                bbox_vol_mm3 = float(bbox_mm[0] * bbox_mm[1] * bbox_mm[2])
                mesh_vol_mm3 = rep["volume_mm3"] or 0.0
                hollow_ratio = None
                if bbox_vol_mm3 > 0 and mesh_vol_mm3 is not None:
                    hollow_ratio = max(0.0, 1.0 - (mesh_vol_mm3 / bbox_vol_mm3))
                rep["hollow_ratio"] = hollow_ratio
                rep["bbox_cm"] = [round(x / 10.0, 2) for x in bbox_mm]
                rep["volume_cm3"] = round(mesh_vol_mm3 / 1000.0, 2) if mesh_vol_mm3 else None

                checks = rep["checks"]
                rep["planter_fitness_score"] = int(sum(1 for v in checks.values() if v))
                is_functional = bool(
                    rep["is_watertight"]
                    or (
                        (hollow_ratio is not None and hollow_ratio >= 0.30)
                        and checks["has_drain"]
                        and checks["fits_3_4_pot"]
                    )
                )
                rep["is_functional_planter"] = is_functional

                # Build concise qc_notes
                notes_parts = []
                notes_parts.append(f"wt={rep['is_watertight']}")
                if hollow_ratio is not None:
                    notes_parts.append(f"hollow={hollow_ratio:.2f}")
                notes_parts.append(f"fits={checks['fits_3_4_pot']}")
                notes_parts.append(f"drain={checks['has_drain']}")
                notes_parts.append(f"stable={checks['stable_base']}")
                notes_parts.append(
                    f"bbox={rep['bbox_cm'][0]}x{rep['bbox_cm'][1]}x{rep['bbox_cm'][2]}cm"
                )
                if rep["failures"]:
                    notes_parts.append("fail=" + ",".join(rep["failures"]))
                rep["qc_notes"] = " | ".join(notes_parts)

                (report_dir / f"{p.id}.json").write_text(json.dumps(rep, indent=2))
                self.stdout.write(
                    f"   functional={is_functional}  wt={rep['is_watertight']}  "
                    f"hollow={hollow_ratio}  fits={checks['fits_3_4_pot']}  "
                    f"drain={checks['has_drain']}  vol_cm3={rep['volume_cm3']}"
                )
                if rep["failures"]:
                    self.stdout.write(f"   failures: {rep['failures']}")

                # Persist onto Product
                if not opts["no_persist"]:
                    from decimal import Decimal
                    p.is_functional_planter = is_functional
                    if rep["volume_cm3"] is not None:
                        p.volume_cm3 = Decimal(str(rep["volume_cm3"]))
                    p.qc_notes = rep["qc_notes"]
                    p.save(update_fields=[
                        "is_functional_planter", "volume_cm3", "qc_notes", "updated_at",
                    ])

                all_reports.append(rep)
            except Exception as e:
                logger.exception("QC failed for product %s", p.id)
                self.stdout.write(self.style.ERROR(f"   QC failed: {e}"))
                all_reports.append({"product_id": p.id, "name": p.name, "error": str(e)})

        summary_path.write_text(json.dumps(all_reports, indent=2, default=str))
        n_pass = sum(1 for r in all_reports if r.get("pass"))
        n_func = sum(1 for r in all_reports if r.get("is_functional_planter"))
        self.stdout.write(self.style.SUCCESS(
            f"\nSummary: strict-pass={n_pass}/{len(all_reports)}  "
            f"functional-planter={n_func}/{len(all_reports)}"
        ))
        self.stdout.write(f"Report: {summary_path}")
