from django.contrib import admin
from .models import Product, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "in_stock", "created_at")
    list_filter = ("category", "in_stock")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)
    fields = ("product", "quantity", "unit_price_snapshot", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_email", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("customer_email", "customer_name", "stripe_payment_intent_id", "shapeways_order_id")
    readonly_fields = ("token", "stripe_payment_intent_id", "created_at", "updated_at", "subtotal", "total")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "unit_price_snapshot")
    search_fields = ("order__customer_email", "product__name")
