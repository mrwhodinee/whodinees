"""Multi-category refactor.

- Creates the Category model.
- Seeds live categories (Planters, Decor) and coming-soon placeholders.
- Replaces Product.category (CharField) with a FK to Category.
  Existing string values are mapped: "planter" -> Planters, "decor" -> Decor.
- Adds Product.featured and Product.display_order for merchandising.
"""
import django.db.models.deletion
from django.db import migrations, models


CATEGORY_SEED = [
    # (slug, name, tagline, live, display_order)
    ("planters", "Planters", "Tiny homes for tiny plants.", True, 1),
    ("decor", "Decor", "Small sculptural friends for shelves and desks.", True, 10),
    ("desk", "Dinees for the Desk", "Functional little desk companions.", False, 20),
    ("kitchen", "Dinees for the Kitchen", "Small helpers for the countertop.", False, 30),
    ("bath", "Dinees for the Bath", "Tiny objects for the steamy room.", False, 40),
    ("plant-accessories", "Plant Accessories", "For the people who already have too many plants.", False, 15),
    ("tech", "Tech Accessories", "Cable wrangling, earbud cradles, little helpers.", False, 50),
    ("seasonal", "Seasonal", "Limited runs for holidays and moods.", False, 60),
]


def seed_and_backfill(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    # Seed categories (idempotent on slug).
    slug_to_obj = {}
    for slug, name, tagline, live, order in CATEGORY_SEED:
        obj, _ = Category.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "tagline": tagline, "live": live, "display_order": order},
        )
        slug_to_obj[slug] = obj

    # Backfill FK from the old CharField values stored in `category_legacy`.
    planters = slug_to_obj["planters"]
    decor = slug_to_obj["decor"]
    for p in Product.objects.all():
        legacy = (p.category_legacy or "planter").strip().lower()
        if legacy == "decor":
            p.category = decor
        else:
            # planter / other / anything else -> Planters on launch
            p.category = planters
        p.save(update_fields=["category"])


def unseed(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Category.objects.filter(slug__in=[s for s, *_ in CATEGORY_SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_alter_product_image_url"),
    ]

    operations = [
        # 1) Create Category model
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("tagline", models.CharField(blank=True, default="", max_length=200)),
                ("live", models.BooleanField(default=True, help_text="If False, treated as a coming-soon placeholder and hidden from the main nav.")),
                ("display_order", models.PositiveIntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["display_order", "name"],
            },
        ),

        # 2) Rename the old CharField column so we can add a new FK of the same name.
        migrations.RenameField(
            model_name="product",
            old_name="category",
            new_name="category_legacy",
        ),

        # 3) Add new FK `category` (nullable so we can backfill it).
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="store.category",
            ),
        ),

        # 4) Merchandising fields.
        migrations.AddField(
            model_name="product",
            name="featured",
            field=models.BooleanField(default=False, help_text="Highlight on home/shop."),
        ),
        migrations.AddField(
            model_name="product",
            name="display_order",
            field=models.PositiveIntegerField(default=100, help_text="Lower shows first."),
        ),

        # 5) Update ordering.
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["display_order", "-created_at"]},
        ),

        # 6) Seed categories + backfill FKs.
        migrations.RunPython(seed_and_backfill, unseed),

        # 7) Drop the legacy CharField now that FK is populated.
        migrations.RemoveField(
            model_name="product",
            name="category_legacy",
        ),
    ]
