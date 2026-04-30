"""SECURE portrait views - UUID tokens + email verification.

SECURITY MODEL:
- All portrait endpoints use UUID token instead of integer ID
- All requests MUST include customer email for verification
- Mismatches return 404 (never 403) - don't reveal record exists
- Only the customer who created the portrait can access it
"""
import logging
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import PetPortrait, PortraitOrder
from . import views as legacy_views  # Import existing views

logger = logging.getLogger(__name__)


def verify_portrait_access(portrait: PetPortrait, email: str) -> bool:
    """Verify customer email matches portrait owner.
    
    Returns True if authorized, False otherwise.
    """
    if not email:
        return False
    return portrait.customer_email.lower() == email.strip().lower()


def get_verified_portrait(token: str, email: str) -> PetPortrait:
    """Get portrait by token and verify email.
    
    Raises Http404 if not found or email doesn't match.
    Never returns 403 - always 404 to prevent enumeration.
    """
    try:
        portrait = PetPortrait.objects.get(token=token)
    except PetPortrait.DoesNotExist:
        raise Http404("Portrait not found")
    
    if not verify_portrait_access(portrait, email):
        # Return 404, not 403 - don't reveal the record exists
        raise Http404("Portrait not found")
    
    return portrait


# ============================================================================
# SECURE ENDPOINTS - All use UUID token + email verification
# ============================================================================

# CREATE remains the same - generates new portrait with token
create_portrait = legacy_views.create_portrait


@api_view(["GET"])
@permission_classes([AllowAny])
def get_portrait(request, token):
    """GET /api/portraits/<uuid>/ - requires email verification."""
    email = request.GET.get('email', '').strip()
    
    if not email:
        return Response({"detail": "Email required"}, status=400)
    
    portrait = get_verified_portrait(token, email)
    
    # Call the existing get_portrait logic but with our verified portrait
    # We temporarily patch the portrait_id parameter
    from types import SimpleNamespace
    fake_request = SimpleNamespace(**{
        key: getattr(request, key) for key in dir(request) 
        if not key.startswith('_')
    })
    fake_request.GET = request.GET
    fake_request.data = request.data
    
    # Import the actual serializer and logic
    from .serializers import PetPortraitSerializer
    from . import views as v
    
    # Re-implement get_portrait logic with our verified portrait
    # (Can't call legacy view because it expects portrait_id)
    
    # TEMPORARY WORKAROUND for deposit polling
    if portrait.status == "deposit_pending" and not portrait.deposit_paid and portrait.deposit_payment_intent_id:
        try:
            import stripe
            from django.conf import settings
            from .services import meshy_portrait
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            pi = stripe.PaymentIntent.retrieve(portrait.deposit_payment_intent_id)
            if pi.status == "succeeded":
                logger.info(f"Polling detected successful payment for portrait {portrait.token}")
                portrait.deposit_paid = True
                try:
                    task_ids = meshy_portrait.submit_variants(portrait.uploaded_photo.path, n=1)
                except Exception as e:
                    logger.exception(f"Meshy variant submission failed: {e}")
                    task_ids = []
                portrait.meshy_variants = [
                    {"task_id": tid, "status": "PENDING", "progress": 0, "preview_url": "", "glb_url": ""}
                    for tid in task_ids
                ]
                portrait.status = "generating" if task_ids else portrait.status
                portrait.save(update_fields=["deposit_paid", "meshy_variants", "status", "updated_at"])
        except Exception as e:
            logger.warning(f"Failed to poll Stripe: {e}")
    
    # Refresh Meshy status
    if portrait.status == "generating" and portrait.meshy_variants:
        if v._refresh_variant_statuses(portrait):
            terminal = {"SUCCEEDED", "SUCCESS", "COMPLETED", "FAILED", "CANCELED", "EXPIRED", "ERROR"}
            good = {"SUCCEEDED", "SUCCESS", "COMPLETED"}
            statuses = [(var.get("status") or "").upper() for var in portrait.meshy_variants]
            if all(s in terminal for s in statuses) and any(s in good for s in statuses):
                portrait.status = "awaiting_approval"
        portrait.save(update_fields=["meshy_variants", "status", "updated_at"])
    
    return Response(PetPortraitSerializer(portrait).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def start_generation(request, token):
    """POST /api/portraits/<uuid>/start-generation - requires email."""
    email = request.data.get('email', '').strip()
    portrait = get_verified_portrait(token, email)
    
    # Call legacy logic with verified portrait
    # Copy the logic from views.start_generation
    from .services import meshy_portrait
    
    if portrait.status != "deposit_pending":
        return Response({"detail": f"Cannot start from status={portrait.status}"}, status=400)
    
    if not portrait.deposit_paid:
        return Response({"detail": "Deposit not paid"}, status=400)
    
    try:
        task_ids = meshy_portrait.submit_variants(portrait.uploaded_photo.path, n=1)
    except Exception as e:
        logger.exception("Meshy submission failed")
        return Response({"detail": f"Meshy API error: {e}"}, status=500)
    
    portrait.meshy_variants = [
        {"task_id": tid, "status": "PENDING", "progress": 0, "preview_url": "", "glb_url": ""}
        for tid in task_ids
    ]
    portrait.status = "generating"
    portrait.save(update_fields=["meshy_variants", "status", "updated_at"])
    
    from .serializers import PetPortraitSerializer
    return Response(PetPortraitSerializer(portrait).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def approve_variant(request, token):
    """POST /api/portraits/<uuid>/approve - requires email."""
    email = request.data.get('email', '').strip()
    portrait = get_verified_portrait(token, email)
    
    if portrait.status not in ("awaiting_approval", "approved"):
        return Response({"detail": f"Cannot approve from status={portrait.status}"}, status=400)
    
    task_id = request.data.get("task_id", "").strip()
    if not task_id:
        return Response({"detail": "task_id required"}, status=400)
    
    # Verify task_id is in variants
    found = False
    for v in portrait.meshy_variants:
        if v.get("task_id") == task_id:
            found = True
            break
    
    if not found:
        return Response({"detail": "Invalid task_id"}, status=400)
    
    portrait.selected_variant_task_id = task_id
    portrait.status = "approved"
    portrait.approved_at = legacy_views.timezone.now()
    portrait.save(update_fields=["selected_variant_task_id", "status", "approved_at", "updated_at"])
    
    from .serializers import PetPortraitSerializer
    return Response(PetPortraitSerializer(portrait).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def create_portrait_order(request, token):
    """POST /api/portraits/<uuid>/order - requires email."""
    email = request.data.get('email', '').strip()
    portrait = get_verified_portrait(token, email)
    
    # Delegate to existing order creation logic
    # But we need to adapt it...
    # For now, just verify access and call the old function
    # (This is complex - might need full reimplementation)
    
    # Re-implement the order creation here
    from decimal import Decimal
    from .services import pricing, metal_prices, email as portrait_email
    from .serializers import PortraitOrderSerializer
    import stripe
    from django.conf import settings
    
    if portrait.status != "approved":
        return Response({"detail": "Portrait must be approved first"}, status=400)
    
    if not portrait.selected_variant_task_id:
        return Response({"detail": "No variant selected"}, status=400)
    
    # Get GLB URL
    glb_url = None
    for v in portrait.meshy_variants:
        if v.get("task_id") == portrait.selected_variant_task_id:
            glb_url = v.get("glb_url")
            break
    
    if not glb_url:
        return Response({"detail": "Selected variant GLB not available"}, status=500)
    
    # Extract order parameters
    material = request.data.get("material", "").strip()
    size_mm = int(request.data.get("size_mm", 40))
    
    # Validate material
    if material not in dict(PortraitOrder.MATERIAL_CHOICES):
        return Response({"detail": "Invalid material"}, status=400)
    
    # Calculate pricing
    try:
        breakdown = pricing.calculate_portrait_pricing(
            glb_url=glb_url,
            material=material,
            size_mm=size_mm
        )
    except Exception as e:
        logger.exception("Pricing calculation failed")
        return Response({"detail": f"Pricing error: {e}"}, status=500)
    
    # Create order
    order = PortraitOrder.objects.create(
        portrait=portrait,
        material=material,
        size_mm=size_mm,
        **breakdown
    )
    
    # Add shipping from request (email already verified above)
    order.shipping_name = request.data.get("shipping_name", "")
    order.shipping_address1 = request.data.get("shipping_address1", "")
    order.shipping_address2 = request.data.get("shipping_address2", "")
    order.shipping_city = request.data.get("shipping_city", "")
    order.shipping_region = request.data.get("shipping_region", "")
    order.shipping_postcode = request.data.get("shipping_postcode", "")
    order.shipping_country = request.data.get("shipping_country", "US")
    order.save()
    
    # Get publishable key for Stripe
    publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    
    # Create Stripe PaymentIntent
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        pi = stripe.PaymentIntent.create(
            amount=int(order.retail_price * 100),
            currency="usd",
            metadata={
                "portrait_order_id": str(order.id),
                "portrait_order_token": str(order.token),
                "portrait_id": str(portrait.id),
                "flow": "portrait_order",
            }
        )
        order.stripe_payment_intent_id = pi.id
        order.save(update_fields=["stripe_payment_intent_id"])
    except Exception as e:
        logger.exception("Stripe PaymentIntent creation failed")
        return Response({"detail": f"Payment setup failed: {e}"}, status=500)
    
    return Response({
        "order": PortraitOrderSerializer(order).data,
        "client_secret": pi.client_secret,
        "publishable_key": publishable_key
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def calculate_portrait_price(request, token):
    """POST /api/portraits/<uuid>/calculate-price - requires email."""
    email = request.data.get('email', '').strip()
    portrait = get_verified_portrait(token, email)
    
    # Get GLB URL
    glb_url = None
    for v in portrait.meshy_variants:
        if v.get("task_id") == portrait.selected_variant_task_id:
            glb_url = v.get("glb_url")
            break
    
    if not glb_url:
        return Response({"detail": "No GLB available"}, status=400)
    
    material = request.data.get("material", "").strip()
    size_mm = int(request.data.get("size_mm", 40))
    
    from .services import pricing
    
    try:
        breakdown = pricing.calculate_portrait_pricing(glb_url, material, size_mm)
        return Response(breakdown)
    except Exception as e:
        logger.exception("Price calculation failed")
        return Response({"detail": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def proxy_glb(request, token):
    """GET /api/portraits/<uuid>/model.glb - proxies Meshy GLB with CORS headers."""
    email = request.GET.get('email', '').strip()
    portrait = get_verified_portrait(token, email)
    
    # Find selected variant GLB
    glb_url = None
    for v in portrait.meshy_variants:
        if v.get("task_id") == portrait.selected_variant_task_id:
            glb_url = v.get("glb_url")
            break
    
    if not glb_url:
        raise Http404("GLB not available")
    
    import requests
    from django.http import HttpResponse
    
    try:
        resp = requests.get(glb_url, stream=True, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch GLB from Meshy: {e}")
        raise Http404("GLB download failed")
    
    response = HttpResponse(resp.iter_content(chunk_size=8192), content_type='model/gltf-binary')
    response['Access-Control-Allow-Origin'] = '*'
    response['Content-Disposition'] = 'inline'
    
    return response


# ============================================================================
# ENDPOINTS THAT DON'T NEED EMAIL VERIFICATION
# ============================================================================

# These are public or have their own auth
pricing_view = legacy_views.pricing_view
portrait_stripe_webhook = legacy_views.portrait_stripe_webhook
submit_review = legacy_views.submit_review
get_reviews = legacy_views.get_reviews
