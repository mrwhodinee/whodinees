"""Test Instagram API connection and credentials.

Usage:
    python manage.py test_instagram
"""

from django.core.management.base import BaseCommand
from marketing import instagram


class Command(BaseCommand):
    help = 'Test Instagram API connection'

    def handle(self, *args, **options):
        self.stdout.write("Testing Instagram API connection...")
        
        try:
            # Test connection
            if instagram.test_connection():
                self.stdout.write(self.style.SUCCESS('✓ Connection successful'))
            else:
                self.stdout.write(self.style.ERROR('✗ Connection failed'))
                return
            
            # Get account info
            info = instagram.get_account_info()
            self.stdout.write("\nAccount Info:")
            self.stdout.write(f"  Username: @{info.get('username')}")
            self.stdout.write(f"  Name: {info.get('name')}")
            self.stdout.write(f"  Followers: {info.get('followers_count'):,}")
            self.stdout.write(f"  Following: {info.get('follows_count'):,}")
            self.stdout.write(f"  Media count: {info.get('media_count'):,}")
            
            self.stdout.write(self.style.SUCCESS('\n✓ Instagram API is configured and working'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: {e}'))
            self.stdout.write('\nCheck your environment variables:')
            self.stdout.write('  - INSTAGRAM_ACCESS_TOKEN')
            self.stdout.write('  - INSTAGRAM_ACCOUNT_ID')
