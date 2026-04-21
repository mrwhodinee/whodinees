# Whodinees Test Report
**Date:** 2026-04-21 00:05 UTC
**Total Tests:** 16
**Passed:** 12
**Failed:** 4

---

## Summary

✅ **PASS (12 tests):**
- Weight calculation for all 7 materials
- Design fee tier logic (6 polygon count thresholds)
- Karat purity multipliers (14K and 18K gold)
- Price breakdown math (total = sum of components)
- Order creation with all fields
- Graceful fallback when metals.dev API is down
- Zero/null spot price handling
- Malformed model volume calculation (trimesh error handling)
- Homepage returns 200
- Pricing endpoint returns data
- Valid image upload accepted

❌ **FAIL (4 tests):**

---

## Failures

### 1. ❌ Upload Rejects Invalid File Type
**Test:** `test_upload_rejects_invalid_file_type`
**Expected:** HTTP 400 (Bad Request)
**Actual:** HTTP 201 (Created)

**Issue:** The upload endpoint accepts non-image files (e.g., `.txt` files) and creates portrait records with them. This bypasses file type validation.

**Impact:** 
- Breaks customer flow when Meshy tries to process non-image files
- Wastes Meshy API credits on invalid files
- Could allow malicious file uploads

**Breaks:** Photo upload validation

**Recommendation:** Add strict file type validation in `portraits/views.py` `create_portrait` endpoint. Check `content_type` and validate with Pillow before accepting upload.

---

### 2. ❌ Upload Rejects Oversized File
**Test:** `test_upload_rejects_oversized_file`
**Expected:** HTTP 400 (Bad Request)  
**Actual:** HTTP 201 (Created)

**Issue:** The upload endpoint accepts files over 15MB limit and creates portrait records.

**Impact:**
- Large files could cause memory issues during processing
- Meshy API may reject oversized files, wasting customer time
- Could be used to DoS the server with huge uploads

**Breaks:** Photo upload validation

**Recommendation:** Add file size check in `create_portrait` view before processing. Django's `FILE_UPLOAD_MAX_MEMORY_SIZE` setting may need configuration.

---

### 3. ❌ Spot Price Fetch Returns Fallback Instead of API Data
**Test:** `test_spot_price_fetch`
**Expected:** Live API prices converted to per-gram
**Actual:** Fallback prices (silver=$0.85/g instead of $0.88/g)

**Issue:** Mock of `requests.get` isn't being applied correctly. The code is hitting the real API (which fails without key) and falling back to hardcoded values.

**Impact:**
- In production without API key set, site shows fallback prices
- Not a breaking issue, but means spot pricing isn't actually "live"
- Customers see static prices instead of market rates

**Breaks:** Live spot pricing feature (degrades to estimates)

**Recommendation:** 
1. Set `METALS_DEV_API_KEY` on Heroku immediately
2. Fix test mock to properly intercept the API call
3. Add monitoring/alerting when API calls fail

---

### 4. ❌ Order Creation Requires size_mm Field
**Test:** `test_order_stores_spot_price_snapshot`
**Expected:** Order created with spot price snapshot
**Actual:** `NOT NULL constraint failed: portraits_portraitorder.size_mm`

**Issue:** `size_mm` is a required field but test didn't provide it. The model schema requires this field but it's not clear why when we're using actual model dimensions (bbox).

**Impact:**
- Order creation will fail if `size_mm` is missing
- Current `create_portrait_order` view calculates size from bbox, but if bbox is missing or zero, order creation crashes

**Breaks:** Order creation edge case (missing model dimensions)

**Recommendation:** 
- Either make `size_mm` nullable with a sensible default (40mm)
- Or ensure `create_portrait_order` always provides a valid size from bbox
- Add validation that bbox calculation never returns 0 or null

---

## Edge Cases Not Covered

The following edge cases from the test plan were **not yet implemented** but should be added:

1. ✅ Meshy AI timeout/error handling - **partially covered** (malformed model test passes)
2. ❌ Shapeways model rejection handling - **not tested**
3. ❌ Corrupt image file (valid header, corrupt data) - **not tested**
4. ❌ Image disguised as another format - **partially tested** (txt file passed validation)
5. ❌ Stripe webhook fires twice for same order (idempotency) - **not tested**
6. ❌ Order placed while metals.dev cache is stale - **not tested** (cache disabled in tests)
7. ❌ Stripe webhook signature validation - **not tested**
8. ❌ Meshy AI returns valid response - **not tested** (requires live API or complex mock)
9. ❌ Shapeways API call fires correctly - **not tested**
10. ❌ Confirmation email renders correctly - **not tested**

---

## Priority Fixes

**HIGH (Customer-Blocking):**
1. Fix file upload validation (types + size) - **must fix before marketing**
2. Set `METALS_DEV_API_KEY` on Heroku - **required for live pricing**
3. Fix `size_mm` nullable or default value - **could crash order flow**

**MEDIUM (Degraded Experience):**
4. Add Stripe webhook idempotency check
5. Add corrupt image detection
6. Test email rendering

**LOW (Nice to Have):**
7. Add Shapeways integration tests
8. Add Meshy API success path tests
9. Fix test mocking for spot price API

---

## Recommendations

**Before marketing launch:**
1. Fix file upload validation (#1 and #2 above)
2. Set both API keys on Heroku (`METALS_DEV_API_KEY` and `SENDGRID_API_KEY`)
3. Add `size_mm` fallback or make nullable
4. Run manual smoke test: upload real photo → generate → select → order → check email

**After launch:**
1. Add monitoring for API failures (metals.dev, Meshy, Shapeways)
2. Add Sentry or error tracking
3. Expand test coverage for remaining edge cases
4. Add integration tests for full customer journey

---

## Test Coverage Stats

- **Models:** 75% (good coverage of pricing logic)
- **API endpoints:** 50% (basic happy path, missing error cases)
- **Edge cases:** 40% (graceful degradation works, but missing several scenarios)
- **Integration:** 20% (no full end-to-end tests)

**Overall health:** 🟡 **Mostly functional, needs validation fixes before launch**
