"""
Abandoned upload recovery system.

Tracks customers who upload photos but don't complete orders,
then sends automated recovery emails via SendGrid.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from .models import PetPortrait
from .services import email as portrait_email, metal_prices

logger = logging.getLogger(__name__)


def find_abandoned_uploads():
    """
    Find portraits that are abandoned at various stages.
    
    Returns:
        dict: {
            '24h': QuerySet of portraits abandoned ~24h ago,
            '72h': QuerySet of portraits abandoned ~72h ago
        }
    """
    now = timezone.now()
    
    # 24 hour window: 23-25 hours ago
    window_24h_start = now - timedelta(hours=25)
    window_24h_end = now - timedelta(hours=23)
    
    # 72 hour window: 71-73 hours ago
    window_72h_start = now - timedelta(hours=73)
    window_72h_end = now - timedelta(hours=71)
    
    # Portraits that are abandoned (status: awaiting_approval or approved but not ordered)
    # and were created in the time window
    abandoned_24h = PetPortrait.objects.filter(
        Q(status='awaiting_approval') | Q(status='approved'),
        created_at__gte=window_24h_start,
        created_at__lte=window_24h_end,
    ).exclude(
        # Exclude if they already have an order
        orders__isnull=False
    )
    
    abandoned_72h = PetPortrait.objects.filter(
        Q(status='awaiting_approval') | Q(status='approved'),
        created_at__gte=window_72h_start,
        created_at__lte=window_72h_end,
    ).exclude(
        orders__isnull=False
    )
    
    return {
        '24h': abandoned_24h,
        '72h': abandoned_72h
    }


def send_24h_recovery_email(portrait):
    """
    Send first recovery email 24 hours after upload.
    
    Reminds customer their model was generated and shows material options.
    """
    try:
        # Track abandoned upload in GA4 (server-side event)
        # Note: For now, just log it. Full GA4 server-side tracking requires Measurement Protocol API
        logger.info(f"[GA4] upload_abandoned event - portrait {portrait.id} at 24h stage")
        # Get current silver spot price for urgency
        silver_price = metal_prices.get_spot_price('silver')
        
        first_name = portrait.pet_name or 'there'
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #8a5cff;">Your custom piece is waiting, {first_name} ✨</h1>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            We generated your 3D model yesterday, but noticed you haven't placed your order yet.
          </p>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            Your model is ready to be printed in your choice of material:
          </p>
          
          <ul style="font-size: 16px; color: #1b1530; line-height: 1.8;">
            <li><strong>Sterling Silver</strong> — Live price today: ${silver_price:.2f}/g</li>
            <li><strong>14K Gold</strong> — Investment-quality precious metal</li>
            <li><strong>Platinum</strong> — The ultimate heirloom piece</li>
          </ul>
          
          <div style="margin: 32px 0;">
            <a href="https://whodinees.com/portraits/{portrait.id}" style="display: inline-block; background: #8a5cff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600;">
              View Your Model & Choose Material →
            </a>
          </div>
          
          <p style="font-size: 14px; color: #5a527a; line-height: 1.6;">
            Precious metal prices change daily based on live spot rates. Your price is locked in when you order.
          </p>
          
          <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; color: #5a527a; font-size: 14px;">
            <p>Questions? Reply to this email or visit <a href="https://whodinees.com" style="color: #8a5cff;">whodinees.com</a></p>
            <p style="margin-top: 16px;">— The Whodinees team</p>
          </div>
        </div>
        """
        
        success = portrait_email._send(
            portrait.customer_email,
            f"Your custom piece is waiting, {first_name}",
            html
        )
        
        if success:
            logger.info(f"24h recovery email sent to {portrait.customer_email} (portrait {portrait.id})")
        
        return success
        
    except Exception as e:
        logger.exception(f"Failed to send 24h recovery email for portrait {portrait.id}: {e}")
        return False


def send_72h_recovery_email(portrait):
    """
    Send second recovery email 72 hours after upload.
    
    Emphasizes investment angle and price volatility.
    """
    try:
        # Get current prices for comparison
        silver_price = metal_prices.get_spot_price('silver')
        gold_price = metal_prices.get_spot_price('gold')
        
        first_name = portrait.pet_name or 'there'
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #8a5cff;">Spot prices change daily — lock in your piece</h1>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            Hi {first_name},
          </p>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            Your 3D model is still waiting, but we wanted to remind you that <strong>precious metal prices fluctuate daily</strong>.
          </p>
          
          <div style="background: #f9f7ff; padding: 20px; border-radius: 12px; margin: 24px 0;">
            <h3 style="color: #1b1530; margin-top: 0;">Today's Live Spot Prices:</h3>
            <table style="width: 100%; font-size: 16px;">
              <tr>
                <td style="padding: 8px 0;"><strong>Silver:</strong></td>
                <td style="padding: 8px 0; text-align: right;">${silver_price:.2f}/gram</td>
              </tr>
              <tr>
                <td style="padding: 8px 0;"><strong>Gold:</strong></td>
                <td style="padding: 8px 0; text-align: right;">${gold_price:.2f}/gram</td>
              </tr>
            </table>
          </div>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            When you order, your price is <strong>locked at the current market rate</strong>. Your piece becomes a permanent reflection of today's precious metal value.
          </p>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            This isn't just jewelry — it's an investment-quality piece priced at live spot rates.
          </p>
          
          <div style="margin: 32px 0;">
            <a href="https://whodinees.com/portraits/{portrait.id}" style="display: inline-block; background: #8a5cff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600;">
              Complete Your Order Today →
            </a>
          </div>
          
          <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; color: #5a527a; font-size: 14px;">
            <p>Questions? Reply to this email or visit <a href="https://whodinees.com" style="color: #8a5cff;">whodinees.com</a></p>
            <p style="margin-top: 16px;">— The Whodinees team</p>
          </div>
        </div>
        """
        
        success = portrait_email._send(
            portrait.customer_email,
            "Spot prices change daily — lock in your piece",
            html
        )
        
        if success:
            logger.info(f"72h recovery email sent to {portrait.customer_email} (portrait {portrait.id})")
        
        return success
        
    except Exception as e:
        logger.exception(f"Failed to send 72h recovery email for portrait {portrait.id}: {e}")
        return False


def process_abandoned_uploads():
    """
    Main function to process abandoned uploads.
    
    Should be run via cron job or scheduled task.
    
    Returns:
        dict: Stats about emails sent
    """
    abandoned = find_abandoned_uploads()
    
    stats = {
        '24h_found': abandoned['24h'].count(),
        '24h_sent': 0,
        '72h_found': abandoned['72h'].count(),
        '72h_sent': 0,
    }
    
    # Send 24h recovery emails
    for portrait in abandoned['24h']:
        if send_24h_recovery_email(portrait):
            stats['24h_sent'] += 1
    
    # Send 72h recovery emails
    for portrait in abandoned['72h']:
        if send_72h_recovery_email(portrait):
            stats['72h_sent'] += 1
    
    logger.info(f"Abandoned upload recovery complete: {stats}")
    return stats
