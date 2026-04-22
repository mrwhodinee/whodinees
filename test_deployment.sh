#!/bin/bash
# Smoke test critical endpoints after deployment

set -e

BASE_URL="${1:-https://whodinees.com}"

echo "🧪 Running deployment smoke tests against: $BASE_URL"
echo ""

# Test 1: Homepage loads
echo "✓ Testing homepage..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Homepage failed with HTTP $HTTP_CODE"
    exit 1
fi
echo "  ✓ Homepage: 200 OK"

# Test 2: API pricing endpoint
echo "✓ Testing pricing API..."
PRICING=$(curl -s "$BASE_URL/api/pricing/portrait")
if ! echo "$PRICING" | grep -q "spot_prices"; then
    echo "❌ Pricing API failed - missing spot_prices"
    exit 1
fi
echo "  ✓ Pricing API: Returns spot prices"

# Test 3: Static files
echo "✓ Testing static assets..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/showcase/golden-retriever.jpg")
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Static files failed with HTTP $HTTP_CODE"
    exit 1
fi
echo "  ✓ Static assets: 200 OK"

# Test 4: Admin login page
echo "✓ Testing admin..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/")
if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "302" ]; then
    echo "❌ Admin failed with HTTP $HTTP_CODE"
    exit 1
fi
echo "  ✓ Admin: $HTTP_CODE (OK)"

# Test 5: Portrait upload endpoint exists
echo "✓ Testing portrait API..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/portraits/")
if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "405" ]; then
    echo "❌ Portrait API failed with HTTP $HTTP_CODE"
    exit 1
fi
echo "  ✓ Portrait API: $HTTP_CODE (OK)"

echo ""
echo "✅ All smoke tests passed!"
