"""Reposition 10 products for honest launch (Path 1)."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Product, Category


class Command(BaseCommand):
    help = "Launch updates: reposition products as decor/sculptures in 'Shop' category."

    def handle(self, *args, **opts):
        shop, _ = Category.objects.update_or_create(
            slug='shop',
            defaults={'name': 'Shop', 'tagline': 'Tiny 3D-printed objects. Made to order.', 'live': True, 'display_order': 1},
        )
        Category.objects.filter(slug='planters').update(live=False)
        Category.objects.filter(slug='decor').update(live=False)

        updates = {
            'prism-planter': ('Prism', Decimal('16.00'), "A crisp geometric dinee with clean pentagonal facets. Small, sculptural, sits quietly on a shelf. 3D printed to order in durable plastic. About 8–10 cm."),
            'hex-hut': ('Hex Hut', Decimal('16.00'), "A tiny faceted hut of a thing. Six crisp sides, minimalist lines, just the right amount of presence. 3D printed to order in durable plastic. About 8–10 cm."),
            'low-poly-orb': ('Low-Poly Orb', Decimal('18.00'), "A little faceted sphere that catches light at every angle. A small object with big magic. 3D printed to order in durable plastic. About 8–10 cm."),
            'cat-napper-planter': ('Cat Napper', Decimal('20.00'), "A sleepy little cat curled up like it owns the shelf. Smooth rounded forms, stubborn personality. 3D printed to order in durable plastic. About 8–10 cm."),
            'froggy-pot': ('Froggy', Decimal('20.00'), "A cheerful little frog with big round eyes and arms wrapped around itself. A small friend that earns its spot. 3D printed to order in durable plastic. About 8–10 cm."),
            'bear-hug-pot': ('Bear Hug', Decimal('20.00'), "A chubby bear mid-hug. Rounded, friendly, low-key charming. 3D printed to order in durable plastic. About 8–10 cm."),
            'daisy-crown-planter': ('Daisy Crown', Decimal('18.00'), "A little crown of daisies. Clean, modern, cheerful. 3D printed to order in durable plastic. About 8–10 cm."),
            'rose-relief-planter': ('Rose Relief', Decimal('22.00'), "Embossed rose petals spiralling up the sides. A touch of softness for any shelf. 3D printed to order in durable plastic. About 8–10 cm."),
            'tulip-trio': ('Tulip Trio', Decimal('22.00'), "Three stylized tulip buds sharing one base. A small bouquet you don't have to water. 3D printed to order in durable plastic. About 8–10 cm."),
            'lotus-bowl': ('Lotus', Decimal('22.00'), "Open lotus petals forming soft walls. Quietly sculptural. 3D printed to order in durable plastic. About 8–10 cm."),
        }
        updated = 0
        for slug, (name, price, desc) in updates.items():
            try:
                p = Product.objects.get(slug=slug)
                p.name = name
                p.price = price
                p.description = desc
                p.category = shop
                p.is_functional_planter = False
                p.material = 'Durable nylon plastic'
                p.pricing_source = 'launch_estimate'
                p.qc_notes = 'Launch batch — decor/sculpture, not a functional planter.'
                p.save()
                updated += 1
                self.stdout.write(f'✓ {slug} -> {name} ${price}')
            except Product.DoesNotExist:
                self.stdout.write(f'✗ {slug} NOT FOUND')
        self.stdout.write(f'\nUpdated {updated}/{len(updates)} products in "Shop".')
