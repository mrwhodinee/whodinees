"""Live precious metal spot pricing via metals.dev API.

Caches prices for 60 seconds to avoid hitting rate limits.
"""
from __future__ import annotations
import time
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

METALS_API_BASE = "https://api.metals.dev/v1"
CACHE_TTL_SECONDS = 60

# Material densities in g/cm³
MATERIAL_DENSITIES = {
    "plastic": 1.2,  # typical PLA/ABS
    "silver": 10.36,  # sterling silver
    "gold_14k_yellow": 13.07,
    "gold_14k_rose": 13.07,
    "gold_14k_white": 13.07,
    "gold_18k_yellow": 15.58,
    "platinum": 21.40,
}

# Karat purity multipliers for gold
GOLD_PURITY = {
    "14k": 0.583,  # 14/24
    "18k": 0.750,  # 18/24
}

DESIGN_FEE_TIERS = {
    "simple": 25,
    "moderate": 45,
    "complex": 75,
}


def _get_api_key() -> str:
    key = settings.METALS_DEV_API_KEY
    if not key:
        raise RuntimeError("METALS_DEV_API_KEY not configured")
    return key


def get_spot_prices() -> dict[str, float]:
    """Fetch live spot prices for silver, gold, platinum in USD per gram.
    
    Returns dict like:
        {"silver": 0.87, "gold": 72.50, "platinum": 31.20}
    
    Cached for 60 seconds.
    """
    cache_key = "metals_spot_prices"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        # metals.dev returns prices in USD per troy ounce by default
        # 1 troy ounce = 31.1035 grams
        # API key goes in query params, not headers
        resp = requests.get(
            f"{METALS_API_BASE}/latest",
            params={"api_key": _get_api_key(), "currency": "USD", "unit": "toz"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Extract prices per troy ounce
        metals = data.get("metals", {})
        silver_toz = metals.get("silver", 0)
        gold_toz = metals.get("gold", 0)
        platinum_toz = metals.get("platinum", 0)
        
        # Convert to per gram
        prices = {
            "silver": silver_toz / 31.1035 if silver_toz else 0,
            "gold": gold_toz / 31.1035 if gold_toz else 0,
            "platinum": platinum_toz / 31.1035 if platinum_toz else 0,
        }
        
        cache.set(cache_key, prices, CACHE_TTL_SECONDS)
        return prices
        
    except Exception as e:
        logger.exception("Failed to fetch metal spot prices: %s", e)
        # Return stale cache if available, otherwise fallback prices
        fallback = cache.get(cache_key + "_stale")
        if fallback:
            return fallback
        return {
            "silver": 0.85,  # fallback approximations
            "gold": 70.00,
            "platinum": 30.00,
        }


def calculate_material_weight(volume_cm3: float, material: str) -> float:
    """Calculate weight in grams given volume and material."""
    density = MATERIAL_DENSITIES.get(material, 1.0)
    return volume_cm3 * density


def calculate_material_cost(weight_grams: float, material: str, spot_prices: dict | None = None) -> float:
    """Calculate material cost in USD.
    
    For precious metals: weight × spot price per gram × purity multiplier
    For plastic: fixed nominal cost
    """
    if material == "plastic":
        return 2.00  # nominal plastic cost
    
    if spot_prices is None:
        spot_prices = get_spot_prices()
    
    # Map material to base metal and purity
    if material == "silver":
        base = "silver"
        purity = 1.0
    elif material.startswith("gold_14k"):
        base = "gold"
        purity = GOLD_PURITY["14k"]
    elif material.startswith("gold_18k"):
        base = "gold"
        purity = GOLD_PURITY["18k"]
    elif material == "platinum":
        base = "platinum"
        purity = 1.0
    else:
        return 0.0
    
    spot_per_gram = spot_prices.get(base, 0)
    return weight_grams * spot_per_gram * purity


def determine_complexity_tier(polycount: int) -> str:
    """Auto-classify model complexity based on polygon count."""
    if polycount < 10000:
        return "simple"
    elif polycount < 30000:
        return "moderate"
    else:
        return "complex"


def get_design_fee(complexity: str) -> float:
    """Get design fee for complexity tier."""
    return DESIGN_FEE_TIERS.get(complexity, 45)


def calculate_full_pricing(
    volume_cm3: float,
    polycount: int,
    material: str,
    shapeways_production_cost: float = 0.0,
) -> dict:
    """Calculate complete pricing breakdown.
    
    Returns:
        {
            "material": "silver",
            "volume_cm3": 0.85,
            "weight_grams": 8.81,
            "polycount": 25000,
            "complexity": "moderate",
            "spot_price_per_gram": 0.87,
            "material_cost": 7.66,
            "shapeways_cost": 48.00,
            "design_fee": 45.00,
            "total": 100.66
        }
    """
    spot_prices = get_spot_prices()
    weight = calculate_material_weight(volume_cm3, material)
    material_cost = calculate_material_cost(weight, material, spot_prices)
    complexity = determine_complexity_tier(polycount)
    design_fee = get_design_fee(complexity)
    
    # Get relevant spot price for display
    if material == "silver":
        spot_display = spot_prices["silver"]
    elif material.startswith("gold"):
        spot_display = spot_prices["gold"]
    elif material == "platinum":
        spot_display = spot_prices["platinum"]
    else:
        spot_display = 0.0
    
    total = material_cost + shapeways_production_cost + design_fee
    
    return {
        "material": material,
        "volume_cm3": round(volume_cm3, 2),
        "weight_grams": round(weight, 2),
        "polycount": polycount,
        "complexity": complexity,
        "spot_price_per_gram": round(spot_display, 2),
        "material_cost": round(material_cost, 2),
        "shapeways_cost": round(shapeways_production_cost, 2),
        "design_fee": round(design_fee, 2),
        "total": round(total, 2),
    }
