"""Publish scheduled Instagram posts that are ready.

Run this via cron every 5-15 minutes:
    */10 * * * * cd /app && python manage.py publish_scheduled_posts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from marketing.models import InstagramPost
from marketing import instagram
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Publish Instagram posts that are scheduled for now or earlier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be published without actually publishing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find posts ready to publish
        ready_posts = InstagramPost.objects.filter(
            status='scheduled'
        ).filter(
            models.Q(scheduled_for__lte=timezone.now()) | models.Q(scheduled_for__isnull=True)
        )
        
        if not ready_posts.exists():
            self.stdout.write(self.style.SUCCESS('No posts ready to publish'))
            return
        
        self.stdout.write(f"Found {ready_posts.count()} post(s) ready to publish")
        
        for post in ready_posts:
            try:
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Would publish: {post.caption[:50]}...")
                    continue
                
                self.stdout.write(f"Publishing: {post.caption[:50]}...")
                
                # Mark as publishing
                post.status = 'publishing'
                post.save()
                
                # Publish to Instagram
                media_id = instagram.publish_photo(
                    image_url=post.image_url,
                    caption=post.caption
                )
                
                # Update post with Instagram data
                post.status = 'published'
                post.instagram_media_id = media_id
                post.published_at = timezone.now()
                post.error_message = ''
                post.save()
                
                self.stdout.write(self.style.SUCCESS(f'✓ Published: {media_id}'))
                
            except Exception as e:
                logger.exception(f"Failed to publish post {post.id}")
                post.status = 'failed'
                post.error_message = str(e)
                post.save()
                self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Completed. {ready_posts.filter(status="published").count()} published.'))
