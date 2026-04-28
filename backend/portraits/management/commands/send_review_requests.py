"""
Django management command to send review request emails.

Run via: python manage.py send_review_requests
Or via Heroku Scheduler: heroku run python backend/manage.py send_review_requests
"""
from django.core.management.base import BaseCommand
from portraits.review_system import process_review_requests


class Command(BaseCommand):
    help = 'Send review request emails to customers 7 days after delivery'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Processing review requests...'))
        
        stats = process_review_requests()
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ Review request processing complete:\n"
            f"  - Orders found: {stats['found']}\n"
            f"  - Emails sent: {stats['sent']}"
        ))
