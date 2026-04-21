"""Portrait order confirmation emails with pricing breakdown."""
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


MATERIAL_LABEL = {
    "plastic": "Plastic",
    "silver": "Sterling Silver",
    "gold_14k_yellow": "14K Yellow Gold",
    "gold_14k_rose": "14K Rose Gold",
    "gold_14k_white": "14K White Gold",
    "gold_18k_yellow": "18K Yellow Gold",
    "platinum": "Platinum",
}


def send_portrait_order_confirmation(order) -> bool:
    """Send order confirmation with full pricing breakdown for investment documentation."""
    material_name = MATERIAL_LABEL.get(order.material, order.material)
    
    # Build pricing breakdown HTML
    metal_name = ""
    if order.material == "silver":
        metal_name = "Silver"
    elif order.material.startswith("gold"):
        metal_name = "Gold"
    elif order.material == "platinum":
        metal_name = "Platinum"
    
    breakdown_rows = f"""
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Material weight:</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{order.weight_grams}g</strong></td></tr>
    """
    
    if order.spot_price_per_gram > 0:
        breakdown_rows += f"""
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">{metal_name} spot price:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.spot_price_per_gram}/g (live)</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Material cost:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.material_cost}</td></tr>
        """
    else:
        breakdown_rows += f"""
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Material cost:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.material_cost}</td></tr>
        """
    
    breakdown_rows += f"""
        <tr style="background: #fafafa;"><td colspan="2" style="padding: 4px;"></td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Production & casting (Shapeways):</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.shapeways_cost}</td></tr>
        <tr style="background: #fafafa;"><td colspan="2" style="padding: 4px;"></td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Design fee:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.design_fee}</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">AI model generation:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.ai_processing_fee}</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Platform & processing:</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${order.platform_fee}</td></tr>
        <tr style="background: #fafafa;"><td colspan="2" style="padding: 4px;"></td></tr>
        <tr style="font-weight: 700; font-size: 1.1em;"><td style="padding: 12px 8px; border-top: 2px solid #8a5cff;">Total:</td><td style="padding: 12px 8px; border-top: 2px solid #8a5cff;">${order.retail_price} USD</td></tr>
    """
    
    from django.utils import timezone
    order_date = order.spot_price_date or order.created_at or timezone.now()
    
    investment_note = ""
    if order.material != "plastic" and order.spot_price_per_gram > 0:
        investment_note = f"""
        <div style="background: #f9f7ff; padding: 16px; border-radius: 12px; margin-top: 24px;">
            <p style="margin: 0; color: #5a527a; font-size: 14px; line-height: 1.6;">
                Your price includes live {metal_name} spot price on {order_date.strftime('%B %d, %Y')}, 
                Shapeways production and casting, AI model generation from your photo, and our platform fee. 
                The metal value of your piece reflects today's market rate.
            </p>
        </div>
        """
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h1 style="color: #8a5cff;">Your Whodinees Portrait Order ✨</h1>
      <p style="font-size: 16px; color: #1b1530;">Thanks for your order! We're creating your custom {material_name} portrait.</p>
      
      <h2 style="color: #1b1530; margin-top: 32px;">Order #{order.id}</h2>
      
      <h3 style="color: #1b1530; margin-top: 24px;">Price Breakdown</h3>
      <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        {breakdown_rows}
      </table>
      
      {investment_note}
      
      <h3 style="color: #1b1530; margin-top: 32px;">Shipping Address</h3>
      <div style="background: #f9f7ff; padding: 16px; border-radius: 12px;">
        <p style="margin: 0; line-height: 1.6;">
          {order.shipping_name}<br/>
          {order.shipping_address1}<br/>
          {(order.shipping_address2 + '<br/>') if order.shipping_address2 else ''}
          {order.shipping_city}, {order.shipping_region} {order.shipping_postcode}<br/>
          {order.shipping_country}
        </p>
      </div>
      
      <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; color: #5a527a; font-size: 14px;">
        <p>We'll send you another email when your portrait ships.</p>
        <p style="margin-top: 16px;">Questions? Reply to this email or visit <a href="https://whodinees.com" style="color: #8a5cff;">whodinees.com</a></p>
        <p style="margin-top: 24px;">— The Whodinees team</p>
      </div>
    </div>
    """
    
    return _send(
        order.portrait.customer_email,
        f"Your Whodinees portrait order #{order.id}",
        html
    )
