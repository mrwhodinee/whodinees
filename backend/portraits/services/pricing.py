"""Portrait pricing calculator.

Formula:
    retail = design_fee + (metal_weight_g * spot_price_per_g) + (shapeways_cost * 1.4)

Design fees (per material):
    plastic  = $60
    bronze   = $100
    silver   = $180
    gold_14k = $299
    platinum = $499

Estimated metal volume per size: we use a compact figurine estimate
(figurine bounding box × fill factor × density). Good enough for retail
quoting until Shapeways returns a per-model quote.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from .metal_prices import get_metal_prices, get_price_per_gram

DESIGN_FEES = {
    "plastic":  Decimal("60.00"),
    "bronze":   Decimal("100.00"),
    "silver":   Decimal("180.00"),
    "gold_14k": Decimal("299.00"),
    "platinum": Decimal("499.00"),
}

# Density in g/cm³
DENSITY = {
    "plastic":  1.2,
    "bronze":   8.8,
    "silver":  10.5,
    "gold_14k": 13.5,
    "platinum": 21.5,
}

# Rough Shapeways base cost per cm³ (USD) — conservative estimates, used
# only until we have a real model quote. Plastic is a flat-ish small-object
# estimate; metals via Shapeways casting services are pricey per cm³.
SHAPEWAYS_COST_PER_CM3 = {
    "plastic":   1.00,
    "bronze":   18.00,
    "silver":   22.00,
    "gold_14k": 45.00,
    "platinum": 60.00,
}

# Available sizes (longest dim, mm)
SIZE_OPTIONS_MM = [40, 60, 80, 100]

# Metal figurines are cast with a hollowed core (Shapeways' casting workflow
# uses wall thickness ~1-2 mm, rest is hollow). Net metal is roughly 8-12%
# of bounding volume for small figurines. Plastic prints are closer to 15-20%
# solid of bbox for durable small figurines.
# NOTE: these are rough first-pass estimates. Final weight/price comes from
# a Shapeways quote on the actual model. Keep conservative so customers
# aren't surprised by a *higher* quote later. (TODO: replace with real
# Shapeways quote integration once an approved GLB has been uploaded.)
FILL_FACTORS = {
    "plastic":  0.18,
    "bronze":   0.07,
    "silver":   0.07,
    "gold_14k": 0.04,  # very thin walls; gold is too precious to go solid
    "platinum": 0.04,
}


def _bbox_volume_cm3(size_mm: int) -> float:
    """Approximate bounding-box volume, cm³, from longest dim."""
    longest_cm = size_mm / 10.0
    # Assume a squat-ish figurine (rough pet proportions): L × 0.6L × 0.6L
    return longest_cm * (longest_cm * 0.6) * (longest_cm * 0.6)


def estimate_weight_g(material: str, size_mm: int) -> float:
    bbox_cm3 = _bbox_volume_cm3(size_mm)
    vol_cm3 = bbox_cm3 * FILL_FACTORS.get(material, 0.15)
    return vol_cm3 * DENSITY.get(material, 1.0)


def estimate_shapeways_cost(material: str, size_mm: int) -> float:
    bbox_cm3 = _bbox_volume_cm3(size_mm)
    # Shapeways charges by net material volume, so use same fill factor.
    vol_cm3 = bbox_cm3 * FILL_FACTORS.get(material, 0.15)
    return vol_cm3 * SHAPEWAYS_COST_PER_CM3.get(material, 0.0)


def _money(val) -> Decimal:
    return Decimal(val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_price(material: str, size_mm: int, prices: dict | None = None) -> dict:
    """Return a full price breakdown for a given material + size."""
    if material not in DESIGN_FEES:
        raise ValueError(f"Unknown material: {material}")
    prices = prices or get_metal_prices()

    design_fee = DESIGN_FEES[material]
    weight_g = estimate_weight_g(material, size_mm)
    per_g = get_price_per_gram(material, prices)
    metal_cost = _money(weight_g * per_g)

    shapeways_raw = estimate_shapeways_cost(material, size_mm)
    shapeways_with_handling = _money(shapeways_raw * 1.4)

    retail = _money(design_fee + metal_cost + shapeways_with_handling)

    return {
        "material": material,
        "size_mm": size_mm,
        "design_fee": str(design_fee),
        "estimated_weight_g": round(weight_g, 2),
        "metal_spot_per_g": per_g,
        "metal_cost": str(metal_cost),
        "shapeways_cost_raw": round(shapeways_raw, 2),
        "shapeways_cost_with_handling": str(shapeways_with_handling),
        "retail": str(retail),
        "currency": "USD",
    }


def compute_all_pricing() -> dict:
    """Full pricing matrix for the pricing page."""
    prices = get_metal_prices()
    out = {
        "metal_prices": prices,
        "sizes_mm": SIZE_OPTIONS_MM,
        "materials": {},
    }
    for material in DESIGN_FEES:
        out["materials"][material] = {
            "design_fee": str(DESIGN_FEES[material]),
            "by_size": {
                str(sz): compute_price(material, sz, prices) for sz in SIZE_OPTIONS_MM
            },
        }
    return out
