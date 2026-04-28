from django.contrib import admin
from .models import PetPortrait, PortraitOrder, PortraitReview


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


@admin.register(PortraitReview)
class PortraitReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "rating", "title", "approved", "featured",
        "has_photo", "review_request_sent_at", "created_at",
    )
    list_filter = ("rating", "approved", "featured")
    search_fields = ("order__portrait__customer_email", "title", "comment")
    readonly_fields = ("review_request_sent_at", "created_at", "updated_at")
    list_editable = ("approved", "featured")
    
    def has_photo(self, obj):
        return bool(obj.customer_photo)
    has_photo.boolean = True
    has_photo.short_description = "Photo uploaded"
