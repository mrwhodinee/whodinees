"""Whodinees Portraits — custom 3D pet figurines from customer photos."""
import uuid
from decimal import Decimal
from django.db import models


class PetPortrait(models.Model):
    """A customer's pet portrait request. Tracks the photo, Meshy variants,
    selected variant, and fulfillment status.
    """

    PET_TYPES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("photo_uploaded", "Photo uploaded"),
        ("photo_rejected", "Photo rejected"),
        ("deposit_pending", "Deposit pending"),
        ("generating", "Generating variants"),
        ("awaiting_approval", "Awaiting approval"),
        ("approved", "Approved"),
        ("ordered", "Ordered"),
        ("fulfilled", "Fulfilled"),
        ("refunded", "Refunded"),
    ]

    # Public opaque token for status URL (so we don't need auth)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    customer_email = models.EmailField()
    pet_name = models.CharField(max_length=80, blank=True, default="")
    pet_type = models.CharField(max_length=16, choices=PET_TYPES, default="dog")

    # Photo: stored on disk for now (Heroku note: ephemeral FS — see PROGRESS
    # for persistent-storage TODO). The photo is a transient intermediate;
    # once Meshy has it we don't strictly need to keep it.
    uploaded_photo = models.ImageField(upload_to="portrait_uploads/", blank=True, null=True)
    photo_quality_score = models.IntegerField(default=0, help_text="0-100")
    photo_issues = models.JSONField(default=list, blank=True)

    # Meshy variants: list of {"task_id": "...", "status": "...", "preview_url": "...", "glb_url": "..."}
    meshy_variants = models.JSONField(default=list, blank=True)
    selected_variant_task_id = models.CharField(max_length=120, blank=True, default="")

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="photo_uploaded")

    deposit_paid = models.BooleanField(default=False)
    deposit_payment_intent_id = models.CharField(max_length=120, blank=True, default="")

    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Portrait #{self.id} {self.pet_name or self.pet_type} ({self.customer_email})"


class PortraitOrder(models.Model):
    """An order for a physical print of an approved PetPortrait."""

    MATERIAL_CHOICES = [
        ("plastic", "Plastic"),
        ("silver", "Sterling Silver"),
        ("gold_14k_yellow", "14K Yellow Gold"),
        ("gold_14k_rose", "14K Rose Gold"),
        ("gold_14k_white", "14K White Gold"),
        ("gold_18k_yellow", "18K Yellow Gold"),
        ("platinum", "Platinum"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("submitted", "Submitted to Shapeways"),
        ("in_production", "In production"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    portrait = models.ForeignKey(PetPortrait, on_delete=models.PROTECT, related_name="orders")
    material = models.CharField(max_length=16, choices=MATERIAL_CHOICES)
    size_mm = models.PositiveIntegerField(help_text="Longest dimension in millimeters")

    # Pricing breakdown (stored at time of order for investment documentation)
    volume_cm3 = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    weight_grams = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    polycount = models.PositiveIntegerField(default=0)
    complexity_tier = models.CharField(max_length=16, default="moderate")  # simple/moderate/complex
    
    spot_price_per_gram = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shapeways_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    design_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    
    pricing_breakdown_json = models.JSONField(default=dict, blank=True, help_text="Full snapshot for customer records")

    # Shipping
    shipping_name = models.CharField(max_length=120, blank=True, default="")
    shipping_address1 = models.CharField(max_length=200, blank=True, default="")
    shipping_address2 = models.CharField(max_length=200, blank=True, default="")
    shipping_city = models.CharField(max_length=100, blank=True, default="")
    shipping_region = models.CharField(max_length=100, blank=True, default="")
    shipping_postcode = models.CharField(max_length=30, blank=True, default="")
    shipping_country = models.CharField(max_length=2, blank=True, default="US")

    # External refs
    shapeways_model_id = models.CharField(max_length=120, blank=True, default="")
    shapeways_order_id = models.CharField(max_length=120, blank=True, default="")
    stripe_payment_intent_id = models.CharField(max_length=120, blank=True, default="")
    tracking_number = models.CharField(max_length=120, blank=True, default="")

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} {self.material} {self.size_mm}mm (${self.retail_price})"
