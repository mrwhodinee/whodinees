"""Whodinees Portraits API views."""
import json
import logging
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import stripe

from .models import PetPortrait, PortraitOrder, PortraitReview
from .serializers import PetPortraitSerializer, PortraitOrderSerializer
from .services import photo_validator, meshy_portrait, pricing, metal_prices, email as portrait_email
from .review_system import generate_discount_code

logger = logging.getLogger(__name__)

DEPOSIT_AMOUNT_USD = 19  # $19 deposit


def _pi_metadata(portrait: PetPortrait) -> dict:
    return {
        "portrait_id": str(portrait.id),
        "portrait_token": str(portrait.token),
        "customer_email": portrait.customer_email,
        "flow": "portrait_deposit",
    }


def _order_metadata(order: PortraitOrder) -> dict:
    return {
        "portrait_order_id": str(order.id),
        "portrait_order_token": str(order.token),
        "portrait_id": str(order.portrait_id),
        "flow": "portrait_order",
    }


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@ratelimit(key='ip', rate='20/d', method='POST', block=True)
def create_portrait(request):
    """POST /api/portraits/ — upload photo, validate, create PetPortrait.
    
    Rate limits: 5 uploads per hour, 20 per day per IP.
    """
    email = (request.data.get("customer_email") or "").strip()
    pet_name = (request.data.get("pet_name") or "").strip()
    pet_type = (request.data.get("pet_type") or "dog").strip()
    photo = request.FILES.get("photo")

    if not email:
        return Response({"detail": "customer_email is required"}, status=400)
    if not photo:
        return Response({"detail": "photo is required"}, status=400)
    if pet_type not in dict(PetPortrait.PET_TYPES):
        return Response({"detail": "Invalid pet_type"}, status=400)
    
    # Strict file validation BEFORE saving to disk
    # 1. Check file size
    if photo.size > 15 * 1024 * 1024:  # 15MB
        return Response({"detail": f"File too large ({photo.size // 1024 // 1024}MB). Maximum 15MB."}, status=400)
    if photo.size < 80 * 1024:  # 80KB
        return Response({"detail": f"File too small ({photo.size // 1024}KB). Minimum 80KB for quality."}, status=400)
    
    # 2. Check content type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if photo.content_type not in allowed_types:
        return Response({"detail": f"Invalid file type: {photo.content_type}. Allowed: JPEG, PNG, WebP."}, status=400)
    
    # 3. Validate it's actually an image by trying to open with Pillow
    try:
        from PIL import Image
        img = Image.open(photo)
        img.verify()  # Checks if file is corrupt
        # Re-open after verify (verify() closes the file)
        photo.seek(0)
        img = Image.open(photo)
        width, height = img.size
        
        # Check minimum dimensions (1200px realistic for modern phone cameras)
        if min(width, height) < 1200:
            return Response({
                "detail": f"Image too small ({width}×{height}px). Minimum 1200px on shortest side."
            }, status=400)
    except Exception as e:
        return Response({"detail": f"Invalid or corrupt image file: {e}"}, status=400)
    finally:
        photo.seek(0)  # Reset for saving

    portrait = PetPortrait.objects.create(
        customer_email=email,
        pet_name=pet_name,
        pet_type=pet_type,
        uploaded_photo=photo,
        status="photo_uploaded",
    )

    # Validate on-disk file
    try:
        passed, score, issues = photo_validator.validate_photo(portrait.uploaded_photo.path)
    except Exception as e:
        logger.exception("Photo validation errored: %s", e)
        passed, score, issues = True, 50, [f"Validation warning: {e}"]

    portrait.photo_quality_score = score
    portrait.photo_issues = issues
    if not passed:
        portrait.status = "photo_rejected"
    portrait.save(update_fields=["photo_quality_score", "photo_issues", "status", "updated_at"])

    return Response(
        {
            "portrait": PetPortraitSerializer(portrait).data,
            "passed": passed,
            "score": score,
            "issues": issues,
        },
        status=http_status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def start_generation(request, portrait_id: int):
    """POST /api/portraits/:id/start-generation — creates $19 Stripe deposit PI."""
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    if portrait.status == "photo_rejected":
        return Response({"detail": "Photo was rejected. Please upload a new photo."}, status=400)
    if portrait.deposit_paid:
        return Response({"detail": "Deposit already paid."}, status=400)

    if not settings.STRIPE_SECRET_KEY:
        return Response({"detail": "Stripe is not configured"}, status=500)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    intent = stripe.PaymentIntent.create(
        amount=DEPOSIT_AMOUNT_USD * 100,
        currency="usd",
        automatic_payment_methods={"enabled": True},
        metadata=_pi_metadata(portrait),
        description="Whodinees Portraits Deposit",
        receipt_email=portrait.customer_email or None,
    )
    portrait.deposit_payment_intent_id = intent["id"]
    portrait.status = "deposit_pending"
    portrait.save(update_fields=["deposit_payment_intent_id", "status", "updated_at"])

    return Response(
        {
            "client_secret": intent["client_secret"],
            "payment_intent_id": intent["id"],
            "amount": DEPOSIT_AMOUNT_USD,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        }
    )


def _refresh_variant_statuses(portrait: PetPortrait) -> bool:
    """Poll each in-flight Meshy variant. Returns True if any status changed."""
    changed = False
    for v in portrait.meshy_variants:
        tid = v.get("task_id")
        cur_status = (v.get("status") or "").upper()
        if not tid or cur_status in ("SUCCEEDED", "SUCCESS", "COMPLETED", "FAILED", "CANCELED", "EXPIRED", "ERROR"):
            continue
        try:
            info = meshy_portrait.poll_task(tid)
        except Exception as e:
            logger.warning("Meshy poll failed for %s: %s", tid, e)
            continue
        if info["status"] != cur_status:
            v["status"] = info["status"]
            v["progress"] = info.get("progress", 0)
            v["preview_url"] = info.get("preview_url") or v.get("preview_url", "")
            v["glb_url"] = info.get("glb_url") or v.get("glb_url", "")
            changed = True
    return changed


@api_view(["GET"])
@permission_classes([AllowAny])
def get_portrait(request, portrait_id: int):
    """GET /api/portraits/:id — status + Meshy progress + preview urls."""
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    # TEMPORARY WORKAROUND: If deposit pending but not paid, check Stripe directly
    # This handles cases where webhook didn't fire
    if portrait.status == "deposit_pending" and not portrait.deposit_paid and portrait.deposit_payment_intent_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            pi = stripe.PaymentIntent.retrieve(portrait.deposit_payment_intent_id)
            if pi.status == "succeeded":
                logger.info(f"Polling detected successful payment for portrait {portrait.id}, starting generation")
                portrait.deposit_paid = True
                # Start Meshy generation
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
            logger.warning(f"Failed to poll Stripe for portrait {portrait.id}: {e}")

    # If we're generating, refresh Meshy task statuses
    if portrait.status == "generating" and portrait.meshy_variants:
        if _refresh_variant_statuses(portrait):
            # If all variants are terminal and at least one succeeded, move to approval
            terminal = {"SUCCEEDED", "SUCCESS", "COMPLETED", "FAILED", "CANCELED", "EXPIRED", "ERROR"}
            good = {"SUCCEEDED", "SUCCESS", "COMPLETED"}
            statuses = [(v.get("status") or "").upper() for v in portrait.meshy_variants]
            if all(s in terminal for s in statuses) and any(s in good for s in statuses):
                portrait.status = "awaiting_approval"
        portrait.save(update_fields=["meshy_variants", "status", "updated_at"])

    return Response(PetPortraitSerializer(portrait).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def approve_variant(request, portrait_id: int):
    """POST /api/portraits/:id/approve — pick winning variant."""
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    if portrait.status not in ("awaiting_approval", "approved"):
        return Response({"detail": f"Cannot approve from status={portrait.status}"}, status=400)

    task_id = (request.data.get("task_id") or "").strip()
    if not task_id:
        return Response({"detail": "task_id is required"}, status=400)

    if not any(v.get("task_id") == task_id for v in portrait.meshy_variants):
        return Response({"detail": "task_id is not a variant of this portrait"}, status=400)

    portrait.selected_variant_task_id = task_id
    portrait.status = "approved"
    portrait.approved_at = timezone.now()
    portrait.save(update_fields=["selected_variant_task_id", "status", "approved_at", "updated_at"])
    return Response(PetPortraitSerializer(portrait).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
@ratelimit(key='ip', rate='10/d', method='POST', block=True)
def create_portrait_order(request, portrait_id: int):
    """POST /api/portraits/:id/order — create PortraitOrder + Stripe PI.
    
    Rate limit: 10 orders per day per IP.
    """
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    if portrait.status not in ("approved", "ordered"):
        return Response({"detail": f"Portrait is not approved (status={portrait.status})"}, status=400)

    if not portrait.selected_variant_task_id:
        return Response({"detail": "No variant selected"}, status=400)

    material = request.data.get("material")
    if material not in dict(PortraitOrder.MATERIAL_CHOICES):
        return Response({"detail": "Invalid material"}, status=400)

    # Get GLB URL from selected variant
    selected = next(
        (v for v in portrait.meshy_variants if v.get("task_id") == portrait.selected_variant_task_id),
        None
    )
    if not selected or not selected.get("glb_url"):
        return Response({"detail": "GLB not available"}, status=400)

    # Calculate pricing using actual model
    try:
        breakdown = pricing.compute_price_for_model(
            glb_url=selected["glb_url"],
            material=material,
            shapeways_cost=48.00,
        )
    except Exception as e:
        logger.exception("Failed to calculate pricing")
        return Response({"detail": f"Pricing calculation failed: {e}"}, status=500)

    # Create order with full pricing breakdown
    from django.utils import timezone
    order = PortraitOrder.objects.create(
        portrait=portrait,
        material=material,
        size_mm=int(max(breakdown["bbox_mm"]) if "bbox_mm" in breakdown else 40),
        volume_cm3=Decimal(str(breakdown["volume_cm3"])),
        weight_grams=Decimal(str(breakdown["weight_grams"])),
        polycount=breakdown["polycount"],
        complexity_tier=breakdown["complexity"],
        spot_price_per_gram=Decimal(str(breakdown["spot_price_per_gram"])),
        spot_price_date=timezone.now(),
        material_cost=Decimal(str(breakdown["material_cost"])),
        shapeways_cost=Decimal(str(breakdown["shapeways_cost"])),
        design_fee=Decimal(str(breakdown["design_fee"])),
        ai_processing_fee=Decimal(str(breakdown["ai_processing_fee"])),
        platform_fee=Decimal(str(breakdown["platform_fee"])),
        retail_price=Decimal(str(breakdown["total"])),
        pricing_breakdown_json=breakdown,
        shipping_name=request.data.get("shipping_name", "") or "",
        shipping_address1=request.data.get("shipping_address1", "") or "",
        shipping_address2=request.data.get("shipping_address2", "") or "",
        shipping_city=request.data.get("shipping_city", "") or "",
        shipping_region=request.data.get("shipping_region", "") or "",
        shipping_postcode=request.data.get("shipping_postcode", "") or "",
        shipping_country=(request.data.get("shipping_country") or "US")[:2],
        status="pending",
    )

    # Stripe PI for the print upsell
    if not settings.STRIPE_SECRET_KEY:
        return Response({"detail": "Stripe not configured"}, status=500)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    amount_cents = int((order.retail_price * 100).to_integral_value())
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        automatic_payment_methods={"enabled": True},
        metadata=_order_metadata(order),
        description=f"Whodinees Portrait — {material} {order.size_mm}mm",
        receipt_email=portrait.customer_email or None,
    )
    order.stripe_payment_intent_id = intent["id"]
    order.save(update_fields=["stripe_payment_intent_id", "updated_at"])

    portrait.status = "ordered"
    portrait.save(update_fields=["status", "updated_at"])

    return Response(
        {
            "order": PortraitOrderSerializer(order).data,
            "price_breakdown": breakdown,
            "client_secret": intent["client_secret"],
            "payment_intent_id": intent["id"],
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        },
        status=http_status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def pricing_view(request):
    """GET /api/pricing/portrait — full pricing matrix."""
    return Response(pricing.compute_all_pricing())


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='30/h', method='POST', block=True)
def calculate_portrait_price(request, portrait_id: int):
    """POST /api/portraits/:id/calculate-price
    
    Rate limit: 30 requests per hour per IP.
    
    Calculate live pricing for a specific portrait + material.
    Body: {"material": "silver"}
    """
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    
    if not portrait.selected_variant_task_id:
        return Response({"detail": "No variant selected"}, status=400)
    
    # Get GLB URL from selected variant
    selected = next(
        (v for v in portrait.meshy_variants if v.get("task_id") == portrait.selected_variant_task_id),
        None
    )
    if not selected or not selected.get("glb_url"):
        return Response({"detail": "GLB not available"}, status=400)
    
    material = request.data.get("material", "silver")
    if material not in dict(PortraitOrder.MATERIAL_CHOICES):
        return Response({"detail": "Invalid material"}, status=400)
    
    # Calculate pricing using actual model
    try:
        breakdown = pricing.compute_price_for_model(
            glb_url=selected["glb_url"],
            material=material,
            shapeways_cost=48.00,
        )
        return Response(breakdown)
    except Exception as e:
        logger.exception("Pricing calculation failed")
        return Response({"detail": str(e)}, status=500)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def portrait_stripe_webhook(request):
    """Webhook endpoint for portrait flows.

    Handles:
      - payment_intent.succeeded with metadata.flow == "portrait_deposit":
        Fire 3 Meshy tasks, mark deposit_paid, status=generating.
      - payment_intent.succeeded with metadata.flow == "portrait_order":
        Mark order as paid (Shapeways submission is a manual review step for now).
    """
    from store.services import stripe_service

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception as e:
        logger.warning("Portrait webhook sig verify failed: %s", e)
        return HttpResponse(status=400)

    event_type = event["type"] if isinstance(event, dict) else event.type
    data_obj = event["data"]["object"] if isinstance(event, dict) else event.data.object
    meta = (data_obj.get("metadata") if isinstance(data_obj, dict) else data_obj.metadata) or {}
    flow = meta.get("flow", "")

    if event_type != "payment_intent.succeeded":
        return HttpResponse(status=200)

    pi_id = data_obj.get("id") if isinstance(data_obj, dict) else data_obj.id

    if flow == "portrait_deposit":
        try:
            portrait = PetPortrait.objects.get(deposit_payment_intent_id=pi_id)
        except PetPortrait.DoesNotExist:
            logger.warning("Deposit webhook for unknown PI %s", pi_id)
            return HttpResponse(status=200)

        if portrait.deposit_paid:
            return HttpResponse(status=200)

        portrait.deposit_paid = True
        try:
            task_ids = meshy_portrait.submit_variants(portrait.uploaded_photo.path, n=1)
        except Exception as e:
            logger.exception("Meshy variant submission failed: %s", e)
            task_ids = []

        portrait.meshy_variants = [
            {"task_id": tid, "status": "PENDING", "progress": 0, "preview_url": "", "glb_url": ""}
            for tid in task_ids
        ]
        portrait.status = "generating" if task_ids else portrait.status
        portrait.save(update_fields=["deposit_paid", "meshy_variants", "status", "updated_at"])

    elif flow == "portrait_order":
        try:
            order = PortraitOrder.objects.get(stripe_payment_intent_id=pi_id)
        except PortraitOrder.DoesNotExist:
            logger.warning("Order webhook for unknown PI %s", pi_id)
            return HttpResponse(status=200)
        if order.status == "pending":
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])
            
            # Generate invoice PDF
            try:
                from .invoice_generator import generate_invoice_pdf, save_invoice_to_order
                pdf_content = generate_invoice_pdf(order)
                save_invoice_to_order(order, pdf_content)
                logger.info(f"Invoice PDF generated for order {order.id}")
            except Exception as e:
                logger.exception(f"Failed to generate invoice PDF: {e}")
            
            # Send confirmation email with pricing breakdown and invoice
            try:
                portrait_email.send_portrait_order_confirmation(order)
            except Exception as e:
                logger.exception("Failed to send order confirmation email: %s", e)
            # TODO: submit to Shapeways once we have the approved GLB's model upload flow

    return HttpResponse(status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def proxy_glb(request, portrait_id):
    """Proxy GLB file from Meshy AI to avoid CORS issues.
    
    GET /api/portraits/{id}/model.glb
    Fetches the GLB from Meshy AI's signed URL and streams it back.
    """
    import requests
    from django.http import Http404
    
    try:
        portrait = PetPortrait.objects.get(id=portrait_id)
    except PetPortrait.DoesNotExist:
        raise Http404("Portrait not found")
    
    # Get the GLB URL from selected variant
    glb_url = None
    if portrait.selected_variant_task_id and portrait.meshy_variants:
        for variant in portrait.meshy_variants:
            if variant.get('task_id') == portrait.selected_variant_task_id:
                glb_url = variant.get('glb_url')
                break
    
    if not glb_url:
        # Fallback to first succeeded variant
        for variant in portrait.meshy_variants or []:
            if variant.get('status') in ['SUCCEEDED', 'SUCCESS', 'COMPLETED']:
                glb_url = variant.get('glb_url')
                break
    
    if not glb_url:
        raise Http404("No GLB model available")
    
    # Fetch from Meshy AI
    try:
        response = requests.get(glb_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Stream back with proper headers
        django_response = HttpResponse(
            response.content,
            content_type='model/gltf-binary'
        )
        django_response['Access-Control-Allow-Origin'] = '*'
        django_response['Cache-Control'] = 'public, max-age=86400'  # Cache for 24h
        return django_response
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch GLB from Meshy: {e}")
        return HttpResponse("Failed to load 3D model", status=502)


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@ratelimit(key='ip', rate='5/h', method='POST')
def submit_review(request, order_token):
    """
    Submit a customer review for an order.
    
    POST /api/portraits/review/{order_token}
    
    Body (multipart/form-data):
    - rating: 1-5 (required)
    - title: Review title (optional)
    - comment: Review text (optional)
    - photo: Customer photo of finished piece (optional)
    """
    try:
        order = PortraitOrder.objects.get(token=order_token)
    except PortraitOrder.DoesNotExist:
        return Response({"error": "Order not found"}, status=http_status.HTTP_404_NOT_FOUND)
    
    # Check if review already exists
    try:
        review = PortraitReview.objects.get(order=order)
        if review.rating > 0:  # Already submitted (rating > 0 means submitted)
            return Response(
                {"error": "Review already submitted for this order"},
                status=http_status.HTTP_400_BAD_REQUEST
            )
    except PortraitReview.DoesNotExist:
        review = PortraitReview(order=order)
    
    # Validate rating
    rating = request.data.get('rating')
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=http_status.HTTP_400_BAD_REQUEST
            )
    except (TypeError, ValueError):
        return Response(
            {"error": "Invalid rating value"},
            status=http_status.HTTP_400_BAD_REQUEST
        )
    
    # Update review
    review.rating = rating
    review.title = request.data.get('title', '').strip()
    review.comment = request.data.get('comment', '').strip()
    
    # Handle photo upload
    has_photo = False
    if 'photo' in request.FILES:
        review.customer_photo = request.FILES['photo']
        has_photo = True
    
    review.save()
    
    logger.info(f"Review submitted for order {order.id}: {rating} stars, photo={has_photo}")
    
    # Generate discount code if they uploaded a photo
    discount_code = None
    if has_photo:
        discount_code = generate_discount_code(order)
    
    return Response({
        "success": True,
        "message": "Thank you for your review!",
        "discount_code": discount_code,
        "discount_message": "Here's your 10% off code for your next order!" if discount_code else None
    }, status=http_status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_reviews(request):
    """
    Get approved reviews for display on homepage.
    
    GET /api/portraits/reviews?featured=true
    """
    reviews = PortraitReview.objects.filter(approved=True, rating__gt=0)
    
    if request.query_params.get('featured') == 'true':
        reviews = reviews.filter(featured=True)
    
    reviews = reviews.select_related('order__portrait').order_by('-created_at')[:20]
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'customer_photo_url': review.customer_photo.url if review.customer_photo else None,
            'material': review.order.material,
            'pet_name': review.order.portrait.pet_name,
            'created_at': review.created_at.isoformat(),
        })
    
    return Response(data)
