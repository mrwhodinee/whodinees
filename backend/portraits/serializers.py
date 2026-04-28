from rest_framework import serializers
from .models import PetPortrait, PortraitOrder


class PetPortraitSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(read_only=True)
    photo_url = serializers.SerializerMethodField()
    glb_url = serializers.SerializerMethodField()

    class Meta:
        model = PetPortrait
        fields = [
            "id", "token", "customer_email", "pet_name", "pet_type",
            "photo_url", "photo_quality_score", "photo_issues",
            "meshy_variants", "selected_variant_task_id",
            "glb_url",
            "status", "deposit_paid",
            "approved_at", "created_at",
        ]
        read_only_fields = [
            "id", "token", "photo_url", "photo_quality_score", "photo_issues",
            "meshy_variants", "selected_variant_task_id",
            "glb_url", "status", "deposit_paid", "approved_at", "created_at",
        ]

    def get_photo_url(self, obj):
        try:
            return obj.uploaded_photo.url if obj.uploaded_photo else ""
        except Exception:
            return ""
    
    def get_glb_url(self, obj):
        """Return proxied GLB URL to avoid CORS issues."""
        # Only return proxy URL if there's a succeeded variant
        if not obj.meshy_variants:
            return None
        
        for variant in obj.meshy_variants:
            if variant.get('status') in ['SUCCEEDED', 'SUCCESS', 'COMPLETED']:
                # Return our proxy endpoint instead of Meshy's direct URL
                request = self.context.get('request')
                if request:
                    from django.urls import reverse
                    path = reverse('portrait-glb-proxy', kwargs={'portrait_id': obj.id})
                    return request.build_absolute_uri(path)
                else:
                    return f"/api/portraits/{obj.id}/model.glb"
        
        return None


class PortraitOrderSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(read_only=True)
    pricing_breakdown = serializers.JSONField(source="pricing_breakdown_json", read_only=True)

    class Meta:
        model = PortraitOrder
        fields = [
            "id", "token", "portrait", "material", "size_mm",
            "volume_cm3", "weight_grams", "polycount", "complexity_tier",
            "spot_price_per_gram", "material_cost", "shapeways_cost",
            "design_fee", "retail_price",
            "pricing_breakdown",
            "shipping_name", "shipping_address1", "shipping_address2",
            "shipping_city", "shipping_region", "shipping_postcode",
            "shipping_country",
            "shapeways_order_id", "tracking_number",
            "status", "created_at",
        ]
        read_only_fields = [
            "id", "token", "volume_cm3", "weight_grams", "polycount",
            "complexity_tier", "spot_price_per_gram", "material_cost",
            "shapeways_cost", "design_fee", "retail_price",
            "pricing_breakdown", "shapeways_order_id",
            "tracking_number", "status", "created_at",
        ]
