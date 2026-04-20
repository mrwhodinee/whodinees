import uuid
from decimal import Decimal
from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("planter", "Planter"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    # Fallback external URL OR data-URL SVG. Meshy thumbnail URLs and SVG data-URLs
    # can be long, so this is a TextField rather than URLField/CharField(200).
    image_url = models.TextField(blank=True, default="")
    stl_file_reference = models.CharField(
        max_length=500, blank=True, default="",
        help_text="Shapeways model id, URL, or local path to STL.",
    )
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="planter")
    in_stock = models.BooleanField(default=True)
    meshy_task_id = models.CharField(max_length=120, blank=True, default="")
    shapeways_model_id = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "product"
            slug = base
            i = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def display_image(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return self.image_url or ""


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("submitted_to_shapeways", "Submitted to Shapeways"),
        ("fulfilled", "Fulfilled"),
        ("failed", "Failed"),
    ]

    # Public lookup token so clients can fetch an order without auth.
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    # Flat address fields are simpler to use with Stripe + Shapeways later.
    shipping_line1 = models.CharField(max_length=200, default="")
    shipping_line2 = models.CharField(max_length=200, blank=True, default="")
    shipping_city = models.CharField(max_length=120, default="")
    shipping_state = models.CharField(max_length=120, blank=True, default="")
    shipping_postal_code = models.CharField(max_length=30, default="")
    shipping_country = models.CharField(max_length=2, default="US")

    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="pending")

    stripe_payment_intent_id = models.CharField(max_length=120, blank=True, default="")
    shapeways_order_id = models.CharField(max_length=120, blank=True, default="")
    tracking_number = models.CharField(max_length=120, blank=True, default="")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="usd")

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} ({self.customer_email}) — {self.status}"

    def recompute_totals(self):
        sub = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.subtotal = sub
        # Simple flat shipping for now; can be replaced with Shapeways quote later.
        if sub > 0 and self.shipping_cost == Decimal("0.00"):
            self.shipping_cost = Decimal("6.00")
        self.total = (self.subtotal + self.shipping_cost).quantize(Decimal("0.01"))
        self.save(update_fields=["subtotal", "shipping_cost", "total", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price_snapshot = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price_snapshot * self.quantity).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"
