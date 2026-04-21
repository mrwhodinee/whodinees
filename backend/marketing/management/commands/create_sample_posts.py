"""Create sample Instagram posts for testing.

Usage:
    python manage.py create_sample_posts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from marketing.models import InstagramPost, ContentQueue
from marketing.instagram import generate_pet_portrait_caption


class Command(BaseCommand):
    help = 'Create sample Instagram posts and queue items for testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample Instagram posts...")
        
        # Sample post 1: Golden Retriever (ready to publish)
        post1 = InstagramPost.objects.create(
            content_type='pet_portrait',
            caption=generate_pet_portrait_caption(
                pet_name="Max",
                material="sterling silver",
                spot_price=2.53
            ),
            image_url='https://whodinees.com/static/showcase/golden-retriever_3d_preview.png',
            alt_text='3D model of a Golden Retriever in sterling silver',
            status='draft',  # Change to 'scheduled' when ready
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created post 1 (Golden Retriever): {post1.id}'))
        
        # Sample post 2: Tabby Cat (scheduled for tomorrow)
        post2 = InstagramPost.objects.create(
            content_type='pet_portrait',
            caption=generate_pet_portrait_caption(
                pet_name="Luna",
                material="14K gold",
                spot_price=153.79
            ),
            image_url='https://whodinees.com/static/showcase/tabby-cat_3d_preview.png',
            alt_text='3D model of a Tabby Cat in 14K gold',
            status='scheduled',
            scheduled_for=timezone.now() + timedelta(days=1, hours=9),  # Tomorrow 9 AM
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created post 2 (Tabby Cat): {post2.id}'))
        
        # Sample post 3: Corgi (scheduled for 2 days from now)
        post3 = InstagramPost.objects.create(
            content_type='pricing_transparency',
            caption=(
                "Why is precious metal jewelry so expensive?\n\n"
                "Most jewelers won't tell you. We will.\n\n"
                "Today's live spot prices:\n"
                "• Silver: $2.53/g\n"
                "• 14K Gold: $153.79/g\n"
                "• Platinum: $66.40/g\n\n"
                "Your pet portrait is priced at actual material weight × today's spot price.\n"
                "No markup games. Full breakdown before checkout.\n\n"
                "This is how it should be. 💎\n\n"
                "whodinees.com"
            ),
            image_url='https://whodinees.com/static/showcase/corgi_3d_preview.png',
            alt_text='3D model of a Corgi with pricing transparency',
            status='scheduled',
            scheduled_for=timezone.now() + timedelta(days=2, hours=14),  # 2 days, 2 PM
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created post 3 (Pricing): {post3.id}'))
        
        # Content queue items
        queue1 = ContentQueue.objects.create(
            title='Process video: Photo to 3D transformation',
            description='Timelapse showing AI generating 3D model from a photo',
            content_type='process_video',
            priority='high',
            notes='Need to create video showing Meshy AI generation in progress',
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created queue item 1: {queue1.title}'))
        
        queue2 = ContentQueue.objects.create(
            title='Material comparison: Silver vs Gold',
            description='Side-by-side showing same model in different metals',
            content_type='material_showcase',
            priority='medium',
            notes='Use same pet in silver and gold. Emphasize weight difference and pricing.',
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created queue item 2: {queue2.title}'))
        
        queue3 = ContentQueue.objects.create(
            title='Customer testimonial from first order',
            description='Share customer photo + review when first order ships',
            content_type='customer_testimonial',
            priority='urgent',
            notes='Wait for first real customer. Get photo + quote.',
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created queue item 3: {queue3.title}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Created {InstagramPost.objects.count()} posts and {ContentQueue.objects.count()} queue items'
        ))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Go to /admin/marketing/instagrampost/')
        self.stdout.write('2. Change post 1 status to "scheduled" to test')
        self.stdout.write('3. Run: python manage.py publish_scheduled_posts --dry-run')
        self.stdout.write('4. When ready: python manage.py publish_scheduled_posts')
