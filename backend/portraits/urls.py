from django.urls import path
from . import views

urlpatterns = [
    path("portraits/", views.create_portrait, name="portrait-create"),
    path("portraits/<int:portrait_id>/", views.get_portrait, name="portrait-detail"),
    path("portraits/<int:portrait_id>/start-generation", views.start_generation, name="portrait-start-gen"),
    path("portraits/<int:portrait_id>/approve", views.approve_variant, name="portrait-approve"),
    path("portraits/<int:portrait_id>/order", views.create_portrait_order, name="portrait-order-create"),
    path("pricing/portrait", views.pricing_view, name="portrait-pricing"),
    path("stripe/portrait-webhook/", views.portrait_stripe_webhook, name="portrait-stripe-webhook"),
]
