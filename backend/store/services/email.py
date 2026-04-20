"""SendGrid email helper. Gracefully no-ops when SENDGRID_API_KEY is not set."""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


def _send(to_email: str, subject: str, html: str, text: str = "") -> bool:
    api_key = settings.SENDGRID_API_KEY
    if not api_key:
        logger.info("SendGrid API key not set — skipping email to %s (subject=%r)", to_email, subject)
        return False
    from_email = settings.SENDGRID_FROM_EMAIL
    body = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": "Whodinees"},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text or _html_to_text(html)},
            {"type": "text/html", "value": html},
        ],
    }
    resp = requests.post(
        SENDGRID_SEND_URL,
        json=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code >= 400:
        logger.error("SendGrid send failed %s: %s", resp.status_code, resp.text[:500])
        return False
    return True


def _html_to_text(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html)


def send_order_confirmation(order) -> bool:
    items_html = "".join(
        f"<li>{it.quantity} × {it.product.name} — ${it.line_total}</li>"
        for it in order.items.select_related("product").all()
    )
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 560px; margin: 0 auto;">
      <h1 style="color: #8a5cff;">Thanks for your order, {order.customer_name}! ✨</h1>
      <p>Small objects, big magic. We're on it.</p>
      <h2>Order #{order.id}</h2>
      <ul>{items_html}</ul>
      <p><strong>Subtotal:</strong> ${order.subtotal}<br/>
         <strong>Shipping:</strong> ${order.shipping_cost}<br/>
         <strong>Total:</strong> ${order.total} {order.currency.upper()}</p>
      <p>Shipping to:<br/>
         {order.shipping_line1}<br/>
         {order.shipping_line2 + '<br/>' if order.shipping_line2 else ''}
         {order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}<br/>
         {order.shipping_country}
      </p>
      <p style="color:#777; font-size: 12px;">— The Whodinees crew</p>
    </div>
    """
    return _send(order.customer_email, f"Your Whodinees order #{order.id}", html)
