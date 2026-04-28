"""
Django management command to send abandoned upload recovery emails.

Run via: python manage.py send_abandoned_recovery
Or via Heroku Scheduler: heroku run python backend/manage.py send_abandoned_recovery
"""
from django.core.management.base import BaseCommand
from portraits.abandoned_uploads import process_abandoned_uploads


class Command(BaseCommand):
    help = 'Send abandoned upload recovery emails (24h and 72h)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Processing abandoned uploads...'))
        
        stats = process_abandoned_uploads()
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ Abandoned upload recovery complete:\n"
            f"  - 24h emails: {stats['24h_sent']}/{stats['24h_found']} sent\n"
            f"  - 72h emails: {stats['72h_sent']}/{stats['72h_found']} sent"
        ))
