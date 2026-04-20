"""Shapeways OAuth2 client_credentials + order submission."""
import logging
import time
import threading
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SHAPEWAYS_BASE = "https://api.shapeways.com"
SHAPEWAYS_TOKEN_URL = f"{SHAPEWAYS_BASE}/oauth2/token"

_token_cache = {"access_token": None, "expires_at": 0.0}
_token_lock = threading.Lock()


def get_access_token(force_refresh: bool = False) -> str:
    """client_credentials OAuth2 flow. Caches token in-process until expiry."""
    client_id = settings.SHAPEWAYS_CLIENT_ID
    client_secret = settings.SHAPEWAYS_CLIENT_SECRET
    if not client_id or not client_secret:
        raise RuntimeError("Shapeways client credentials are not configured")

    with _token_lock:
        now = time.time()
        if (
            not force_refresh
            and _token_cache["access_token"]
            and now < _token_cache["expires_at"] - 30
        ):
            return _token_cache["access_token"]

        resp = requests.post(
            SHAPEWAYS_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=30,
        )
        if resp.status_code != 200:
            logger.error("Shapeways token fetch failed %s: %s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        ttl = int(data.get("expires_in", 3600))
        _token_cache["access_token"] = token
        _token_cache["expires_at"] = now + ttl
        return token


def auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def submit_order(order) -> dict:
    """
    Submit an order to Shapeways. This is a best-effort scaffold:
    in practice each model must exist in a Shapeways account first and be
    assigned a model id. For now we:
      - require every order item's product.shapeways_model_id to be populated
      - fall back to raising if any item lacks one

    Returns the parsed Shapeways API response on success.
    """
    if order.status != "paid":
        raise ValueError(f"Cannot submit order in status {order.status!r}")

    items = list(order.items.select_related("product").all())
    if not items:
        raise ValueError("Order has no items")

    order_items_payload = []
    for it in items:
        model_id = it.product.shapeways_model_id
        if not model_id:
            raise RuntimeError(
                f"Product {it.product.name!r} has no shapeways_model_id; cannot submit"
            )
        order_items_payload.append({
            "modelId": int(model_id),
            "materialId": 6,  # White Natural Versatile Plastic — placeholder default
            "quantity": it.quantity,
        })

    body = {
        "orderItems": order_items_payload,
        "firstName": order.customer_name.split(" ", 1)[0] or order.customer_name,
        "lastName": (order.customer_name.split(" ", 1)[1] if " " in order.customer_name else ""),
        "country": order.shipping_country,
        "state": order.shipping_state,
        "city": order.shipping_city,
        "address1": order.shipping_line1,
        "address2": order.shipping_line2 or "",
        "zipCode": order.shipping_postal_code,
        "phoneNumber": "",
        "paymentVerificationId": order.stripe_payment_intent_id or "",
        "shippingOption": "Cheapest",
    }

    resp = requests.post(
        f"{SHAPEWAYS_BASE}/orders/v1",
        json=body,
        headers=auth_headers(),
        timeout=60,
    )
    if resp.status_code >= 400:
        logger.error("Shapeways order submit failed %s: %s", resp.status_code, resp.text[:800])
        resp.raise_for_status()
    data = resp.json()

    order_id = (
        (data.get("order") or {}).get("orderId")
        or data.get("orderId")
        or ""
    )
    if order_id:
        order.shapeways_order_id = str(order_id)
    order.status = "submitted_to_shapeways"
    order.save(update_fields=["shapeways_order_id", "status", "updated_at"])
    return data


def ping_auth() -> dict:
    """Fetch a token and return a summary dict. Used for health checks."""
    token = get_access_token(force_refresh=True)
    return {
        "ok": bool(token),
        "token_len": len(token) if token else 0,
        "expires_at": _token_cache["expires_at"],
    }
