from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("orders/", views.create_order, name="order-create"),
    path("orders/<uuid:token>/", views.order_detail, name="order-detail"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("health/", views.health, name="health"),
]
