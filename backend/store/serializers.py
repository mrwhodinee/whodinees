from rest_framework import serializers
from .models import Product, Order, OrderItem, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "tagline", "live", "display_order"]


class ProductSerializer(serializers.ModelSerializer):
    image_url_resolved = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "category",        # slug for backwards compat
            "category_slug",
            "category_name",
            "featured",
            "display_order",
            "in_stock",
            "image_url_resolved",
        ]

    def get_image_url_resolved(self, obj):
        url = obj.display_image
        if not url:
            return ""
        request = self.context.get("request")
        if request and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url

    def get_category(self, obj):
        return obj.category.slug if obj.category_id else ""

    def get_category_slug(self, obj):
        return obj.category.slug if obj.category_id else ""

    def get_category_name(self, obj):
        return obj.category.name if obj.category_id else ""


class OrderItemInSerializer(serializers.Serializer):
    product_slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=1, max_value=50)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    shipping_line1 = serializers.CharField(max_length=200)
    shipping_line2 = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    shipping_city = serializers.CharField(max_length=120)
    shipping_state = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    shipping_postal_code = serializers.CharField(max_length=30)
    shipping_country = serializers.CharField(max_length=2, default="US")
    items = OrderItemInSerializer(many=True)


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "unit_price_snapshot", "line_total"]


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "token",
            "customer_name",
            "customer_email",
            "shipping_line1",
            "shipping_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "status",
            "subtotal",
            "shipping_cost",
            "total",
            "currency",
            "items",
            "created_at",
        ]
