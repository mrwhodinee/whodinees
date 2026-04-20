from rest_framework import serializers
from .models import PetPortrait, PortraitOrder


class PetPortraitSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = PetPortrait
        fields = [
            "id", "token", "customer_email", "pet_name", "pet_type",
            "photo_url", "photo_quality_score", "photo_issues",
            "meshy_variants", "selected_variant_task_id",
            "status", "deposit_paid",
            "approved_at", "created_at",
        ]
        read_only_fields = [
            "id", "token", "photo_url", "photo_quality_score", "photo_issues",
            "meshy_variants", "selected_variant_task_id",
            "status", "deposit_paid", "approved_at", "created_at",
        ]

    def get_photo_url(self, obj):
        try:
            return obj.uploaded_photo.url if obj.uploaded_photo else ""
        except Exception:
            return ""


class PortraitOrderSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(read_only=True)

    class Meta:
        model = PortraitOrder
        fields = [
            "id", "token", "portrait", "material", "size_mm",
            "retail_price", "design_fee", "estimated_metal_weight_g",
            "shipping_name", "shipping_address1", "shipping_address2",
            "shipping_city", "shipping_region", "shipping_postcode",
            "shipping_country",
            "shapeways_order_id", "tracking_number",
            "status", "created_at",
        ]
        read_only_fields = [
            "id", "token", "retail_price", "design_fee",
            "estimated_metal_weight_g", "shapeways_order_id",
            "tracking_number", "status", "created_at",
        ]
