from django.urls import path
from . import views
from . import test_views
from . import views_order_status

urlpatterns = [
    path("portraits/", views.create_portrait, name="portrait-create"),
    path("portraits/<int:portrait_id>/", views.get_portrait, name="portrait-detail"),
    path("portraits/<int:portrait_id>/start-generation", views.start_generation, name="portrait-start-gen"),
    path("portraits/<int:portrait_id>/approve", views.approve_variant, name="portrait-approve"),
    path("portraits/<int:portrait_id>/order", views.create_portrait_order, name="portrait-order-create"),
    path("portraits/<int:portrait_id>/calculate-price", views.calculate_portrait_price, name="portrait-calculate-price"),
    path("portraits/<int:portrait_id>/model.glb", views.proxy_glb, name="portrait-glb-proxy"),
    path("portraits/review/<uuid:order_token>", views.submit_review, name="portrait-submit-review"),
    path("portraits/reviews", views.get_reviews, name="portrait-get-reviews"),
    path("pricing/portrait", views.pricing_view, name="portrait-pricing"),
    path("stripe/portrait-webhook/", views.portrait_stripe_webhook, name="portrait-stripe-webhook"),
    # Test endpoints for Sentry (remove after verification)
    path("test/sentry-error", test_views.test_sentry_error, name="test-sentry-error"),
    path("test/sentry-message", test_views.test_sentry_message, name="test-sentry-message"),
    # Order status portal
    path("orders/lookup", views_order_status.order_status_lookup, name="order-status-lookup"),
    path("orders/find", views_order_status.find_orders_by_email, name="find-orders-by-email"),
    path("orders/<uuid:order_token>", views_order_status.order_detail, name="order-detail"),
    path("orders/<uuid:order_token>/invoice", views_order_status.download_invoice, name="download-invoice"),
    path("portraits/<uuid:portrait_token>/model", views_order_status.download_model, name="download-model"),
]
