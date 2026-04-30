# CRITICAL SECURITY FIX - Portrait ID Enumeration

## Problem
All portrait and order endpoints use sequential integer IDs in URLs:
- `/api/portraits/23/` - anyone can enumerate 1, 2, 3... and see all customer data
- `/api/portraits/23/order` - exposes order details
- No email verification required to access portraits

## Current State
✅ Models already have UUID `token` field
❌ Views use integer `portrait_id` parameter
❌ URLs expose integer IDs
❌ No authentication/email verification
❌ React app requests use integer IDs

## Fix Steps

### 1. Update URL patterns (portraits/urls.py)
Change from:
```python
path("portraits/<int:portrait_id>/", views.get_portrait)
```

To:
```python
path("portraits/<uuid:token>/", views.get_portrait_secure)
```

### 2. Update all views to:
- Accept `token` UUID instead of `portrait_id` integer
- Look up by `token` field: `get_object_or_404(PetPortrait, token=token)`
- Verify customer email matches (from request body/header)
- Return 404 (not 403) on auth failure - never reveal record exists

### 3. Add email verification helper
```python
def verify_portrait_access(portrait, request):
    """Verify customer email matches. Returns True if authorized."""
    email = request.data.get('email') or request.GET.get('email') or ''
    return portrait.customer_email.lower() == email.strip().lower()
```

### 4. Update React frontend
- Change all `/api/portraits/${id}/` to `/api/portraits/${token}/`
- Include customer email in all requests
- Update localStorage to store token not ID

### 5. Migration (not needed - token already exists)
Models already have token field, no migration needed.

### 6. Verify with Playwright
- Test `/api/portraits/23/` returns 404
- Test `/api/portraits/<valid-uuid>/` without email returns 404  
- Test `/api/portraits/<valid-uuid>/` with correct email succeeds

## Implementation Priority
🚨 **DO THIS IMMEDIATELY BEFORE ANY MARKETING**

This is a GDPR violation waiting to happen.
