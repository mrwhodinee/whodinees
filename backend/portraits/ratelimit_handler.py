"""
Custom handler for rate limit errors.
Provides friendly error messages and alerts on abuse.
"""
import logging
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def ratelimited_error(request, exception=None):
    """
    Custom handler for django-ratelimit.
    
    Called when a request is blocked by rate limiting.
    """
    # Log the rate limit hit
    ip = get_client_ip(request)
    endpoint = request.path
    logger.warning(f"Rate limit hit: IP {ip} on {endpoint}")
    
    # Check if this IP has hit daily limit (potential abuse)
    # This is a simplified check - in production, track this in Redis/database
    if should_alert_abuse(ip, endpoint):
        send_abuse_alert(ip, endpoint)
    
    # Return friendly error message
    return JsonResponse({
        "error": "rate_limit_exceeded",
        "message": "You have reached the upload limit. Please try again later or contact hello@whodinees.com for assistance."
    }, status=429)


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def should_alert_abuse(ip, endpoint):
    """
    Check if we should send an abuse alert for this IP.
    
    In a real implementation, this would check a cache/database
    to see if this IP has hit the limit multiple times.
    
    For now, always alert on order endpoint abuse (10/day limit).
    """
    return '/order' in endpoint


def send_abuse_alert(ip, endpoint):
    """
    Send Telegram alert about potential abuse.
    
    Alerts Dude when an IP hits daily rate limits repeatedly.
    """
    import os
    import requests
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '1972458437')
    
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping abuse alert")
        return
    
    message = f"⚠️ *Rate Limit Abuse Detected*\n\n"
    message += f"*IP:* `{ip}`\n"
    message += f"*Endpoint:* `{endpoint}`\n"
    message += f"*Action:* IP has hit the daily rate limit\n\n"
    message += "This could indicate scraping, abuse, or a legitimate customer with an issue. "
    message += "Review logs if this persists."
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
        logger.info(f"Abuse alert sent for IP {ip}")
    except Exception as e:
        logger.error(f"Failed to send abuse alert: {e}")
