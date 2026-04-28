"""
Sentry webhook receiver that forwards critical errors to Telegram.
"""
import os
import logging
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '1972458437')


def send_telegram_alert(message):
    """Send alert to Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping alert")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def sentry_webhook(request):
    """
    Receive webhooks from Sentry and forward critical errors to Telegram.
    
    Sentry webhook documentation:
    https://docs.sentry.io/product/integrations/integration-platform/webhooks/
    """
    try:
        payload = json.loads(request.body)
        
        # Extract event details
        action = payload.get('action', 'unknown')
        data = payload.get('data', {})
        
        # Only alert on new issues or regressions
        if action not in ['created', 'reopened']:
            return JsonResponse({"status": "ignored", "reason": f"action={action}"})
        
        issue = data.get('issue', {})
        event = data.get('event', {})
        
        # Get error details
        title = issue.get('title', 'Unknown error')
        culprit = issue.get('culprit', 'Unknown location')
        level = issue.get('level', 'error')
        url = issue.get('permalink', 'No URL')
        
        # Get exception info
        exception_type = None
        exception_value = None
        if event:
            exceptions = event.get('exception', {}).get('values', [])
            if exceptions:
                exc = exceptions[0]
                exception_type = exc.get('type', '')
                exception_value = exc.get('value', '')
        
        # Format message for Telegram
        message = f"🚨 *Sentry Alert: {level.upper()}*\n\n"
        message += f"*Error:* {title}\n"
        if exception_type:
            message += f"*Type:* `{exception_type}`\n"
        if exception_value:
            message += f"*Message:* {exception_value[:200]}\n"
        message += f"*Location:* `{culprit}`\n"
        message += f"\n[View in Sentry]({url})"
        
        # Send to Telegram
        sent = send_telegram_alert(message)
        
        return JsonResponse({
            "status": "ok",
            "telegram_sent": sent,
            "event": title
        })
        
    except Exception as e:
        logger.exception(f"Error processing Sentry webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
