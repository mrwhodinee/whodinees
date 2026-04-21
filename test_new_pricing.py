#!/usr/bin/env python3
"""Test new pricing structure with all materials."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whodinees.settings')
import django
django.setup()

from portraits.services import metals_pricing

# Test materials
materials = [
    "plastic",
    "silver",
    "gold_14k_yellow",
    "gold_14k_rose",
    "gold_14k_white",
    "gold_18k",
    "platinum"
]

# Sample order: 0.85 cm³, 25k polycount
volume = 0.85
polycount = 25000
shapeways_cost = 48.00

print("=" * 80)
print("NEW PRICING STRUCTURE TEST")
print("=" * 80)
print(f"Volume: {volume} cm³")
print(f"Polycount: {polycount}")
print(f"Shapeways cost: ${shapeways_cost}")
print("=" * 80)
print()

for material in materials:
    print(f"Material: {material.upper()}")
    print("-" * 80)
    
    breakdown = metals_pricing.calculate_full_pricing(
        volume_cm3=volume,
        polycount=polycount,
        material=material,
        shapeways_production_cost=shapeways_cost
    )
    
    print(f"  Material weight: {breakdown['weight_grams']}g")
    if breakdown['spot_price_per_gram'] > 0:
        print(f"  {breakdown['metal_name']} spot price: ${breakdown['spot_price_per_gram']}/g (live)")
    print(f"  Material cost: ${breakdown['material_cost']}")
    print(f"  " + "─" * 60)
    print(f"  Production & casting (Shapeways): ${breakdown['shapeways_cost']}")
    print(f"  " + "─" * 60)
    print(f"  Design fee ({breakdown['complexity']}): ${breakdown['design_fee']}")
    print(f"  AI model generation: ${breakdown['ai_processing_fee']}")
    print(f"  Platform & processing: ${breakdown['platform_fee']}")
    print(f"  " + "─" * 60)
    print(f"  TOTAL: ${breakdown['total']}")
    print()

print("=" * 80)
print("TEST COMPLETE - All materials calculated successfully")
print("=" * 80)
