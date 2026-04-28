from django.urls import path
from . import views
from . import test_views

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
]
