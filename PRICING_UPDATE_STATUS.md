# Spot Pricing Implementation Status

## ✅ Completed (Backend Core)

### 1. Metals.dev API Integration
- Added `METALS_DEV_API_KEY` to settings
- Created `metals_pricing.py` service with:
  - Live spot price fetching (60s cache)
  - Material densities for all metals
  - Karat purity multipliers (14k = 58.3%, 18k = 75%)
  - Auto-tiered design fees (simple/$25, moderate/$45, complex/$75)
  - Full transparent pricing calculation

### 2. Mesh Analysis
- Created `mesh_analyzer.py` using trimesh
- Analyzes GLB files to extract:
  - Volume in cm³
  - Polygon count
  - Bounding box dimensions
  - Watertight status

### 3. Database Schema
- Updated `PortraitOrder` model with new fields:
  - `volume_cm3`, `weight_grams`, `polycount`
  - `complexity_tier` (simple/moderate/complex)
  - `spot_price_per_gram`, `material_cost`, `shapeways_cost`
  - `pricing_breakdown_json` (full snapshot)
- Expanded materials to 7 options:
  - Plastic, Sterling Silver
  - 14K Yellow/Rose/White Gold
  - 18K Yellow Gold, Platinum
- Migration created and applied locally

### 4. Updated Services
- Rewrote `pricing.py` to use new system
- Added `compute_price_for_model(glb_url, material)` function
- Updated `compute_all_pricing()` for pricing page

### 5. Serializers
- Updated `PortraitOrderSerializer` to include all new pricing fields
- Exposes `pricing_breakdown` JSON to frontend

## ⚠️ Not Yet Wired Up (Needs Integration)

### Frontend Changes Needed
1. Update material selector in `PortraitCheckout.jsx`:
   - Add new material options (gold variants, 18k, etc.)
   - Remove size selector (use actual model dimensions)
   - Add live price recalculation on material change
   - Show transparent breakdown:
     ```
     Material weight: 4.2g
     Sterling Silver spot: $0.87/g (live)
     Material cost: $3.65
     Production & casting: $48.00
     Design fee (moderate): $45.00
     ────────────────────
     Total: $96.65
     ```

2. Update `PortraitsLanding.jsx` pricing display
3. API integration for live price calc endpoint

### Backend Wiring Needed
1. Add endpoint: `POST /api/portraits/:id/calculate-price`
   - Takes `{"material": "silver"}`
   - Returns full pricing breakdown using GLB
   - See `ADD_TO_VIEWS.py` for implementation

2. Update `create_portrait_order` view:
   - Call `compute_price_for_model()` instead of old estimator
   - Store full breakdown in `pricing_breakdown_json`
   - Populate new fields (volume, weight, polycount, etc.)

3. Email template updates:
   - Add pricing breakdown to confirmation email
   - Include investment documentation text

### Heroku Config
Need to set via CLI or dashboard:
```
METALS_DEV_API_KEY=RZE2CPP9DP2UITKPX9DE523KPX9DE
```

## Files Modified
- `backend/whodinees/settings.py` - added METALS_DEV_API_KEY
- `backend/portraits/models.py` - expanded materials, new pricing fields
- `backend/portraits/serializers.py` - expose pricing breakdown
- `backend/portraits/admin.py` - updated readonly fields
- `backend/portraits/services/metals_pricing.py` - NEW
- `backend/portraits/services/mesh_analyzer.py` - NEW
- `backend/portraits/services/pricing.py` - rewritten

## Testing Checklist
- [ ] metals.dev API returns live prices
- [ ] trimesh can analyze Meshy GLB files
- [ ] Volume calculation is accurate
- [ ] Design fee tiers work correctly
- [ ] Frontend shows breakdown before checkout
- [ ] Order stores full snapshot
- [ ] Confirmation email includes breakdown

## Next Steps
1. Wire up calculate-price endpoint
2. Update frontend material selector
3. Test full flow with real GLB
4. Deploy + set Heroku config var
5. Update confirmation email template
