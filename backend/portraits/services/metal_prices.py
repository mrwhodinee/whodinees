"""Metal spot prices for portrait pricing.

Hardcoded as of 2026-04-20. Cached in Django cache for 1 hour.

TODO: wire a live pricing API (metals-api.com, goldapi.io, or
metals.live). Keys not yet provisioned. For now these values are
reviewed and manually bumped.
"""
from __future__ import annotations
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "portrait_metal_prices_v1"
CACHE_TTL = 3600  # 1 hour

# Hardcoded 2026-04-20 snapshot (USD)
DEFAULT_PRICES = {
    "silver_per_g": 0.964,    # ~$30/oz ÷ 31.1 g/oz
    "silver_per_oz": 30.00,
    "gold_14k_per_g": 55.00,  # alloyed; customer-facing 14K
    "gold_24k_per_g": 94.00,  # spot ref, informational
    "bronze_per_g": 0.40,     # commercial bronze alloy
    "platinum_per_g": 33.00,
    "as_of": "2026-04-20",
    "source": "hardcoded",
}


def get_metal_prices() -> dict:
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    # TODO: fetch live prices here when API is wired.
    prices = dict(DEFAULT_PRICES)
    cache.set(CACHE_KEY, prices, CACHE_TTL)
    return prices


def get_price_per_gram(material: str, prices: dict | None = None) -> float:
    """Return USD per gram for a given material code (see PortraitOrder.MATERIAL_CHOICES)."""
    p = prices or get_metal_prices()
    return {
        "plastic": 0.0,  # plastic priced by Shapeways, no metal
        "bronze": p["bronze_per_g"],
        "silver": p["silver_per_g"],
        "gold_14k": p["gold_14k_per_g"],
        "platinum": p["platinum_per_g"],
    }.get(material, 0.0)
