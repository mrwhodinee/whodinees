"""
Customer review collection system.

Sends post-delivery emails asking for reviews with photo upload incentive.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from .models import PortraitOrder, PortraitReview
from .services import email as portrait_email

logger = logging.getLogger(__name__)


def find_orders_needing_review_request():
    """
    Find orders that should receive a review request.
    
    Criteria:
    - Status: 'delivered'
    - Delivered 7-10 days ago (1 week window)
    - No review exists yet
    - Review request not already sent
    
    Returns:
        QuerySet of PortraitOrder
    """
    now = timezone.now()
    
    # 7-10 day window for review requests
    window_start = now - timedelta(days=10)
    window_end = now - timedelta(days=7)
    
    orders = PortraitOrder.objects.filter(
        status='delivered',
        updated_at__gte=window_start,
        updated_at__lte=window_end,
    ).exclude(
        # Exclude if review already exists
        review__isnull=False
    ).select_related('portrait')
    
    # Filter out orders where we've already sent the request
    # (We'll track this in PortraitReview.review_request_sent_at)
    orders_to_email = []
    for order in orders:
        # Check if we've already sent a review request
        try:
            review = PortraitReview.objects.get(order=order)
            if review.review_request_sent_at:
                continue  # Already sent
        except PortraitReview.DoesNotExist:
            pass  # No review yet, proceed
        
        orders_to_email.append(order)
    
    return orders_to_email


def send_review_request_email(order):
    """
    Send review request email with incentive for photo upload.
    
    Incentive: Upload a photo of your piece, get 10% off your next order.
    """
    try:
        pet_name = order.portrait.pet_name or "your pet"
        material_name = dict(order.MATERIAL_CHOICES).get(order.material, order.material)
        
        # Generate review token for secure submission
        review_url = f"https://whodinees.com/review/{order.token}"
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #8a5cff;">How does your piece look? ✨</h1>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            We hope your {material_name} portrait of {pet_name} arrived safely and looks amazing!
          </p>
          
          <p style="font-size: 16px; color: #1b1530; line-height: 1.6;">
            We'd love to hear what you think. Your feedback helps us improve and helps other customers decide.
          </p>
          
          <div style="background: #f9f7ff; padding: 20px; border-radius: 12px; margin: 24px 0; border: 2px solid #8a5cff;">
            <h3 style="color: #8a5cff; margin-top: 0;">📸 Special Offer: Upload a Photo, Get 10% Off</h3>
            <p style="margin: 0; color: #1b1530; line-height: 1.6;">
              Share a photo of your finished piece and we'll send you a <strong>10% discount code</strong> for your next order.
            </p>
          </div>
          
          <div style="margin: 32px 0; text-align: center;">
            <a href="{review_url}" style="display: inline-block; background: #8a5cff; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 18px;">
              Leave a Review (2 minutes) →
            </a>
          </div>
          
          <p style="font-size: 14px; color: #5a527a; line-height: 1.6; text-align: center;">
            Your honest feedback means everything to us
          </p>
          
          <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; color: #5a527a; font-size: 14px;">
            <p>Questions? Reply to this email or visit <a href="https://whodinees.com" style="color: #8a5cff;">whodinees.com</a></p>
            <p style="margin-top: 16px;">— The Whodinees team</p>
          </div>
        </div>
        """
        
        success = portrait_email._send(
            order.portrait.customer_email,
            f"How does your {material_name} piece look?",
            html
        )
        
        if success:
            # Create/update review record to track that we sent the request
            review, created = PortraitReview.objects.get_or_create(
                order=order,
                defaults={'rating': 0}  # Placeholder until they submit
            )
            review.review_request_sent_at = timezone.now()
            review.save(update_fields=['review_request_sent_at', 'updated_at'])
            
            logger.info(f"Review request email sent to {order.portrait.customer_email} (order {order.id})")
        
        return success
        
    except Exception as e:
        logger.exception(f"Failed to send review request email for order {order.id}: {e}")
        return False


def process_review_requests():
    """
    Main function to send review request emails.
    
    Should be run via cron job or scheduled task.
    
    Returns:
        dict: Stats about emails sent
    """
    orders = find_orders_needing_review_request()
    
    stats = {
        'found': len(orders),
        'sent': 0,
    }
    
    for order in orders:
        if send_review_request_email(order):
            stats['sent'] += 1
    
    logger.info(f"Review request processing complete: {stats}")
    return stats


def generate_discount_code(order):
    """
    Generate a 10% discount code for customers who upload photos.
    
    Format: PHOTO10-{order_id}
    """
    return f"PHOTO10-{order.id}"
