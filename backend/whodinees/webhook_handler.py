"""Unified Stripe webhook handler for all Whodinees payment flows."""
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def unified_stripe_webhook(request):
    """Single webhook endpoint that routes to appropriate handler based on metadata.flow."""
    from store.services import stripe_service
    
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    
    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        return HttpResponse(status=400)
    
    event_type = event["type"] if isinstance(event, dict) else event.type
    data_obj = event["data"]["object"] if isinstance(event, dict) else event.data.object
    meta = (data_obj.get("metadata") if isinstance(data_obj, dict) else data_obj.metadata) or {}
    flow = meta.get("flow", "")
    
    logger.info(f"Webhook received: type={event_type}, flow={flow}")
    
    # Route based on flow
    if flow in ("portrait_deposit", "portrait_order"):
        return _handle_portrait_webhook(event, event_type, data_obj, meta, flow)
    else:
        return _handle_store_webhook(event, event_type, data_obj)


def _handle_portrait_webhook(event, event_type, data_obj, meta, flow):
    """Handle portrait deposit and order webhooks."""
    from portraits.models import PetPortrait, PortraitOrder
    from portraits.services import meshy_portrait, email as portrait_email
    
    if event_type != "payment_intent.succeeded":
        return HttpResponse(status=200)
    
    pi_id = data_obj.get("id") if isinstance(data_obj, dict) else data_obj.id
    
    if flow == "portrait_deposit":
        logger.info(f"Processing portrait deposit webhook for PI {pi_id}")
        try:
            portrait = PetPortrait.objects.get(deposit_payment_intent_id=pi_id)
        except PetPortrait.DoesNotExist:
            logger.warning(f"Deposit webhook for unknown PI {pi_id}")
            return HttpResponse(status=200)
        
        if portrait.deposit_paid:
            logger.info(f"Portrait {portrait.id} deposit already marked paid")
            return HttpResponse(status=200)
        
        portrait.deposit_paid = True
        logger.info(f"Marking portrait {portrait.id} deposit as paid, starting Meshy generation")
        
        try:
            task_ids = meshy_portrait.submit_variants(portrait.uploaded_photo.path, n=1)
            logger.info(f"Meshy tasks created: {task_ids}")
        except Exception as e:
            logger.exception(f"Meshy variant submission failed: {e}")
            task_ids = []
        
        portrait.meshy_variants = [
            {"task_id": tid, "status": "PENDING", "progress": 0, "preview_url": "", "glb_url": ""}
            for tid in task_ids
        ]
        portrait.status = "generating" if task_ids else portrait.status
        portrait.save(update_fields=["deposit_paid", "meshy_variants", "status", "updated_at"])
        logger.info(f"Portrait {portrait.id} updated: deposit_paid=True, status={portrait.status}")
    
    elif flow == "portrait_order":
        logger.info(f"Processing portrait order webhook for PI {pi_id}")
        try:
            order = PortraitOrder.objects.get(stripe_payment_intent_id=pi_id)
        except PortraitOrder.DoesNotExist:
            logger.warning(f"Order webhook for unknown PI {pi_id}")
            return HttpResponse(status=200)
        
        if order.status == "pending":
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])
            logger.info(f"Portrait order {order.id} marked as paid")
            
            try:
                portrait_email.send_portrait_order_confirmation(order)
            except Exception as e:
                logger.exception(f"Failed to send order confirmation email: {e}")
    
    return HttpResponse(status=200)


def _handle_store_webhook(event, event_type, data_obj):
    """Handle legacy store order webhooks."""
    from store.models import Order
    from store.services import shapeways, email as email_service
    
    if event_type != "payment_intent.succeeded":
        return HttpResponse(status=200)
    
    pi_id = data_obj.get("id") if isinstance(data_obj, dict) else data_obj["id"]
    
    logger.info(f"Processing store order webhook for PI {pi_id}")
    try:
        order = Order.objects.get(stripe_payment_intent_id=pi_id)
    except Order.DoesNotExist:
        logger.warning(f"Webhook for unknown PI {pi_id}")
        return HttpResponse(status=200)
    
    if order.status == "pending":
        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])
        logger.info(f"Store order {order.id} marked as paid")
        
        # Try Shapeways submission; swallow errors so webhook stays 2xx.
        try:
            shapeways.submit_order(order)
        except Exception as e:
            logger.exception(f"Shapeways submit failed for order {order.id}: {e}")
            order.status = "failed"
            order.notes = (order.notes or "") + f"\nShapeways error: {e}"
            order.save(update_fields=["status", "notes", "updated_at"])
        
        try:
            email_service.send_order_confirmation(order)
        except Exception:
            logger.exception(f"Order confirmation email failed for order {order.id}")
    
    return HttpResponse(status=200)
