import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product, Order, OrderItem, Category
from .serializers import (
    ProductSerializer,
    OrderCreateSerializer,
    OrderReadSerializer,
    CategorySerializer,
)
from .services import stripe_service, shapeways, email as email_service

logger = logging.getLogger(__name__)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Product.objects.filter(in_stock=True).select_related("category")
        slug = self.request.query_params.get("category")
        if slug:
            qs = qs.filter(category__slug=slug)
        return qs


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Category.objects.all()
        if self.request.query_params.get("live") == "true":
            qs = qs.filter(live=True)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    """Create a pending order + Stripe PaymentIntent. Returns client_secret + order token."""
    ser = OrderCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # Resolve products
    slug_to_qty = {}
    for item in data["items"]:
        slug_to_qty[item["product_slug"]] = slug_to_qty.get(item["product_slug"], 0) + item["quantity"]
    products = list(Product.objects.filter(slug__in=slug_to_qty.keys()))
    if len(products) != len(slug_to_qty):
        missing = set(slug_to_qty) - {p.slug for p in products}
        return Response({"error": f"Unknown products: {sorted(missing)}"}, status=400)

    with transaction.atomic():
        order = Order.objects.create(
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            shipping_line1=data["shipping_line1"],
            shipping_line2=data.get("shipping_line2", ""),
            shipping_city=data["shipping_city"],
            shipping_state=data.get("shipping_state", ""),
            shipping_postal_code=data["shipping_postal_code"],
            shipping_country=data["shipping_country"],
        )
        for p in products:
            qty = slug_to_qty[p.slug]
            OrderItem.objects.create(
                order=order,
                product=p,
                quantity=qty,
                unit_price_snapshot=p.price,
            )
        order.recompute_totals()

    # Create PaymentIntent outside the DB transaction so we don't hold it during network I/O.
    try:
        pi = stripe_service.create_payment_intent_for_order(order)
    except Exception as e:
        logger.exception("Failed to create PaymentIntent for order %s", order.id)
        return Response({"error": f"Payment setup failed: {e}"}, status=502)

    return Response({
        "order_token": str(order.token),
        "order_id": order.id,
        "amount": str(order.total),
        "currency": order.currency,
        "client_secret": pi["client_secret"],
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def order_detail(request, token):
    order = get_object_or_404(Order, token=token)
    return Response(OrderReadSerializer(order).data)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        return HttpResponse(status=400)

    event_type = event["type"] if isinstance(event, dict) else event.type
    data_obj = (event["data"]["object"] if isinstance(event, dict) else event.data.object)

    if event_type == "payment_intent.succeeded":
        pi_id = data_obj.get("id") if isinstance(data_obj, dict) else data_obj["id"]
        try:
            order = Order.objects.get(stripe_payment_intent_id=pi_id)
        except Order.DoesNotExist:
            logger.warning("Webhook for unknown PI %s", pi_id)
            return HttpResponse(status=200)

        if order.status == "pending":
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])

            # Try Shapeways submission; swallow errors so webhook stays 2xx.
            try:
                shapeways.submit_order(order)
            except Exception as e:
                logger.exception("Shapeways submit failed for order %s: %s", order.id, e)
                order.status = "failed"
                order.notes = (order.notes or "") + f"\nShapeways error: {e}"
                order.save(update_fields=["status", "notes", "updated_at"])

            try:
                email_service.send_order_confirmation(order)
            except Exception:
                logger.exception("Order confirmation email failed for order %s", order.id)

    return HttpResponse(status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    out = {"ok": True, "products": Product.objects.count()}
    return Response(out)


def spa_index(request):
    """Serve the React build's index.html for any non-API route.
    When the build is missing (e.g. very early local dev), return a friendly placeholder.
    """
    try:
        tmpl = get_template("index.html")
        html = tmpl.render({}, request)
        return HttpResponse(html)
    except TemplateDoesNotExist:
        return HttpResponse(
            "<!doctype html><html><body style='font-family:sans-serif;padding:2rem'>"
            "<h1>Whodinees</h1><p>small objects, big magic</p>"
            "<p><em>Frontend build not found yet. API: <a href='/api/products/'>/api/products/</a></em></p>"
            "</body></html>",
            content_type="text/html",
        )
