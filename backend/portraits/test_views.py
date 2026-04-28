"""Test views for Sentry error monitoring."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse


@api_view(['GET'])
@permission_classes([AllowAny])
def test_sentry_error(request):
    """Deliberately trigger an error to test Sentry integration."""
    # This will be caught by Sentry
    raise Exception("🚨 Sentry test error - if you see this in Sentry dashboard, integration works!")


@api_view(['GET'])
@permission_classes([AllowAny])
def test_sentry_message(request):
    """Send a test message to Sentry without crashing."""
    import sentry_sdk
    sentry_sdk.capture_message("✅ Sentry test message - integration working!", level="info")
    return Response({"status": "Test message sent to Sentry"})
