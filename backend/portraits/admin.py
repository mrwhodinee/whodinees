from django.contrib import admin
from .models import PetPortrait, PortraitOrder


@admin.register(PetPortrait)
class PetPortraitAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer_email", "pet_name", "pet_type",
        "status", "deposit_paid", "photo_quality_score",
        "selected_variant_task_id", "created_at",
    )
    list_filter = ("status", "pet_type", "deposit_paid")
    search_fields = ("customer_email", "pet_name", "deposit_payment_intent_id", "selected_variant_task_id")
    readonly_fields = ("token", "created_at", "updated_at")


@admin.register(PortraitOrder)
class PortraitOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "portrait", "material", "size_mm", "retail_price",
        "status", "shapeways_order_id", "tracking_number", "created_at",
    )
    list_filter = ("status", "material", "size_mm")
    search_fields = ("portrait__customer_email", "stripe_payment_intent_id", "shapeways_order_id", "tracking_number")
    readonly_fields = ("token", "pricing_breakdown_json", "created_at", "updated_at")
