"""Updated portrait pricing using live spot prices and trimesh volume calculation.

This replaces the old estimate-based system with:
- Live metals.dev spot prices (cached 60s)
- Actual mesh volume from GLB via trimesh
- Auto-tiered design fees based on complexity
- Full transparent breakdown
"""
from __future__ import annotations
from decimal import Decimal
from . import metals_pricing, mesh_analyzer


def compute_price_for_model(
    glb_url: str,
    material: str,
    shapeways_cost: float = 48.00,
) -> dict:
    """Calculate pricing for a specific 3D model.
    
    Args:
        glb_url: URL to GLB file
        material: One of the MATERIAL_DENSITIES keys
        shapeways_cost: Production/casting cost from Shapeways
    
    Returns:
        Full pricing breakdown dict from metals_pricing.calculate_full_pricing
    """
    # Analyze the mesh
    analysis = mesh_analyzer.analyze_glb(glb_url)
    
    # Calculate pricing
    pricing = metals_pricing.calculate_full_pricing(
        volume_cm3=analysis["volume_cm3"],
        polycount=analysis["polycount"],
        material=material,
        shapeways_production_cost=shapeways_cost,
    )
    
    return pricing


def compute_all_pricing() -> dict:
    """Generate pricing matrix for all materials at standard sizes.
    
    Used by the pricing page to show examples. Without a specific model,
    we use typical figurine estimates.
    """
    spot_prices = metals_pricing.get_spot_prices()
    
    # Typical 40mm figurine estimates
    typical_volume_cm3 = 0.85
    typical_polycount = 20000
    typical_shapeways = 48.00
    
    materials_info = {}
    
    for material_key in metals_pricing.MATERIAL_DENSITIES.keys():
        pricing = metals_pricing.calculate_full_pricing(
            volume_cm3=typical_volume_cm3,
            polycount=typical_polycount,
            material=material_key,
            shapeways_production_cost=typical_shapeways,
        )
        
        materials_info[material_key] = {
            "design_fee": pricing["design_fee"],
            "ai_processing_fee": pricing["ai_processing_fee"],
            "platform_fee": pricing["platform_fee"],
            "typical_weight_g": pricing["weight_grams"],
            "spot_price_per_gram": pricing["spot_price_per_gram"],
            "typical_material_cost": pricing["material_cost"],
            "typical_shapeways_cost": pricing["shapeways_cost"],
            "typical_total": pricing["total"],
        }
    
    return {
        "spot_prices": spot_prices,
        "materials": materials_info,
        "note": "Prices for typical 40mm figurine. Final price calculated from your actual model.",
    }
