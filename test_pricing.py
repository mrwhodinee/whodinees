#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whodinees.settings')
django.setup()

from portraits.services import metals_pricing

print("Testing metals pricing...")
prices = metals_pricing.get_spot_prices()
print(f"Spot prices: {prices}")

breakdown = metals_pricing.calculate_full_pricing(
    volume_cm3=0.85,
    polycount=20000,
    material='silver',
    shapeways_production_cost=48.00
)
print(f"\nPricing breakdown for silver:")
for k, v in breakdown.items():
    print(f"  {k}: {v}")
