"""Stripe helpers."""
import logging
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


def _configure():
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent_for_order(order) -> dict:
    """Create a Stripe PaymentIntent for the order. Returns dict with client_secret + id."""
    _configure()
    amount_cents = int((order.total * 100).to_integral_value())
    if amount_cents <= 0:
        raise ValueError("Order total must be > 0 to create a PaymentIntent")

    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=order.currency or "usd",
        automatic_payment_methods={"enabled": True},
        metadata={
            "order_id": str(order.id),
            "order_token": str(order.token),
            "customer_email": order.customer_email,
        },
        receipt_email=order.customer_email or None,
    )
    order.stripe_payment_intent_id = intent["id"]
    order.save(update_fields=["stripe_payment_intent_id", "updated_at"])
    return {"client_secret": intent["client_secret"], "payment_intent_id": intent["id"]}


def construct_webhook_event(payload: bytes, sig_header: str):
    """Verify Stripe webhook signature and return event, or raise."""
    _configure()
    secret = settings.STRIPE_WEBHOOK_SECRET
    if not secret:
        # If no secret configured, parse naively (only acceptable in dev).
        logger.warning("STRIPE_WEBHOOK_SECRET not set; accepting unverified webhook payload")
        import json
        return json.loads(payload.decode("utf-8"))
    return stripe.Webhook.construct_event(payload, sig_header, secret)
