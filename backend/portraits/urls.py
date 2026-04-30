"""SECURE URLs - use UUID tokens instead of integer IDs"""
from django.urls import path
from . import views_secure
from . import test_views
from . import views_order_status

urlpatterns = [
    # Public endpoints
    path("portraits/", views_secure.create_portrait, name="portrait-create"),
    path("portraits/<uuid:token>/", views_secure.get_portrait, name="portrait-detail"),
    path("portraits/<uuid:token>/start-generation", views_secure.start_generation, name="portrait-start-gen"),
    path("portraits/<uuid:token>/approve", views_secure.approve_variant, name="portrait-approve"),
    path("portraits/<uuid:token>/order", views_secure.create_portrait_order, name="portrait-order-create"),
    path("portraits/<uuid:token>/calculate-price", views_secure.calculate_portrait_price, name="portrait-calculate-price"),
    path("portraits/<uuid:token>/model.glb", views_secure.proxy_glb, name="portrait-glb-proxy"),
    
    # Review system
    path("portraits/review/<uuid:order_token>", views_secure.submit_review, name="portrait-submit-review"),
    path("portraits/reviews", views_secure.get_reviews, name="portrait-get-reviews"),
    
    # Pricing
    path("pricing/portrait", views_secure.pricing_view, name="portrait-pricing"),
    
    # Webhooks (no auth needed - Stripe signature verification)
    path("stripe/portrait-webhook/", views_secure.portrait_stripe_webhook, name="portrait-stripe-webhook"),
    
    # Test endpoints
    path("test/sentry-error", test_views.test_sentry_error, name="test-sentry-error"),
    path("test/sentry-message", test_views.test_sentry_message, name="test-sentry-message"),
    
    # Order status portal
    path("orders/lookup", views_order_status.order_status_lookup, name="order-status-lookup"),
    path("orders/find", views_order_status.find_orders_by_email, name="find-orders-by-email"),
    path("orders/<uuid:order_token>", views_order_status.order_detail, name="order-detail"),
    path("orders/<uuid:order_token>/invoice", views_order_status.download_invoice, name="download-invoice"),
    path("portraits/<uuid:portrait_token>/model", views_order_status.download_model, name="download-model"),
]
