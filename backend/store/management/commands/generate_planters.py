"""
python manage.py generate_planters

Generates 10 planter designs via Meshy Text-to-3D API, downloads thumbnails,
and creates Product rows. On any failure we still create a Product with a
placeholder image so the catalog has 10 items.
"""
import logging
import os
import random
import time
import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files import File

from store.models import Product
from store.services import meshy

logger = logging.getLogger(__name__)


PLANTERS = [
    # (theme, name, prompt, price)
    ("geometric", "Prism Planter",       "a small geometric prism planter with a pentagonal cross-section, minimalist, matte white, clean edges, for a tiny succulent", Decimal("24.00")),
    ("geometric", "Hex Hut",              "a small hexagonal planter shaped like a tiny faceted hut, clean geometric facets, matte white, for a small cactus",          Decimal("22.00")),
    ("geometric", "Low-Poly Orb",         "a small low-poly spherical planter, faceted triangular surface, modern minimalist design, for a tiny air plant",              Decimal("26.00")),

    ("animal",    "Cat Napper Planter",   "a small planter shaped like a sleeping cat curled around a bowl, cute stylized, smooth rounded forms, for a small succulent", Decimal("32.00")),
    ("animal",    "Froggy Pot",           "a small planter shaped like a happy little frog sitting with arms around a pot belly, big round eyes, playful stylized",      Decimal("30.00")),
    ("animal",    "Bear Hug Pot",         "a small planter shaped like a cute chubby bear hugging a small pot in front of its belly, rounded friendly design",            Decimal("34.00")),

    ("floral",    "Daisy Crown Planter",  "a small round planter with a sculpted ring of daisies around the top rim, clean modern ceramic look",                         Decimal("28.00")),
    ("floral",    "Rose Relief Planter",  "a small cylindrical planter with embossed rose petals spiralling up the side, elegant floral relief, matte finish",            Decimal("36.00")),
    ("floral",    "Tulip Trio",           "a small planter shaped like three tulip buds grouped together sharing a single base, stylized floral planter",                 Decimal("38.00")),
    ("floral",    "Lotus Bowl",           "a small lotus-flower-shaped planter, open petals forming the bowl, symmetrical, modern organic design",                       Decimal("42.00")),
]


class Command(BaseCommand):
    help = "Generate 10 planter products via Meshy AI (with graceful fallback to placeholders)."

    def add_arguments(self, parser):
        parser.add_argument("--skip-meshy", action="store_true", help="Skip Meshy API and create placeholders only")
        parser.add_argument("--force", action="store_true", help="Regenerate even if products already exist")
        parser.add_argument("--timeout", type=int, default=480, help="Per-task poll timeout (s)")

    def handle(self, *args, **opts):
        skip = opts["skip_meshy"]
        force = opts["force"]
        timeout = opts["timeout"]

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        products_dir = media_root / "products"
        products_dir.mkdir(parents=True, exist_ok=True)

        existing = Product.objects.count()
        if existing >= 10 and not force:
            self.stdout.write(self.style.WARNING(f"Already have {existing} products; use --force to regenerate"))
            return

        if force:
            self.stdout.write("--force: deleting existing products")
            Product.objects.all().delete()

        created = 0
        warnings = []

        for (category, name, prompt, price) in PLANTERS:
            self.stdout.write(f"▶ {name} ({category})")
            product = Product(
                name=name,
                description=self._description_for(name, category, prompt),
                price=price,
                category="planter",
                in_stock=True,
            )

            if skip or not settings.MESHY_API_KEY:
                self._attach_placeholder(product, products_dir, name)
                product.save()
                created += 1
                warnings.append(f"{name}: placeholder (Meshy skipped / no key)")
                continue

            try:
                task_id = meshy.create_text_to_3d_preview(prompt)
                product.meshy_task_id = task_id or ""
                self.stdout.write(f"   meshy task: {task_id}")
                task = meshy.poll_until_done(task_id, timeout_s=timeout, interval_s=8)
                # Save thumbnail
                filename = f"{product.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}.png"
                dest = products_dir / filename
                ok = meshy.download_thumbnail(task, str(dest))
                if ok and dest.exists():
                    with dest.open("rb") as f:
                        product.image.save(filename, File(f), save=False)
                else:
                    self._attach_placeholder(product, products_dir, name)
                    warnings.append(f"{name}: Meshy OK but no thumbnail")
                product.save()
                created += 1
            except Exception as e:
                logger.exception("Meshy generation failed for %s", name)
                warnings.append(f"{name}: Meshy failed — {e}")
                self._attach_placeholder(product, products_dir, name)
                product.save()
                created += 1
                # Small backoff before the next attempt
                time.sleep(2)

        self.stdout.write(self.style.SUCCESS(f"Created {created} products"))
        if warnings:
            self.stdout.write(self.style.WARNING("Warnings:"))
            for w in warnings:
                self.stdout.write(f"  - {w}")

    @staticmethod
    def _description_for(name: str, category: str, prompt: str) -> str:
        vibes = {
            "geometric": "A crisp little geometric planter for the minimalists. Pairs beautifully with a single succulent or a mossy rock — small object, big magic.",
            "animal":    "A tiny friend for your shelf. Made to cradle one small plant like it's their whole world.",
            "floral":    "Petals in place of walls. A little love letter for whatever green thing you tuck inside.",
        }
        return f"{vibes.get(category, '')}\n\n3D printed to order in durable plastic. ~8–12 cm tall.\n\nDesign prompt: {prompt}"

    @staticmethod
    def _attach_placeholder(product: Product, products_dir: Path, name: str) -> None:
        """Generate a minimal 512x512 PNG placeholder with the product name."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (512, 512), (240, 232, 255))  # pale lilac
        draw = ImageDraw.Draw(img)
        # accent circle
        draw.ellipse((96, 96, 416, 416), fill=(199, 175, 255))
        # inner circle
        draw.ellipse((160, 160, 352, 352), fill=(138, 92, 255))
        # text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception:
            font = ImageFont.load_default()
        text = name
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
        except Exception:
            w = len(text) * 14
        draw.text(((512 - w) / 2, 236), text, fill=(255, 255, 255), font=font)
        filename = f"placeholder-{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}.png"
        dest = products_dir / filename
        img.save(dest, format="PNG")
        with dest.open("rb") as f:
            product.image.save(filename, File(f), save=False)
