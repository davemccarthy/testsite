from django.core.management.base import BaseCommand
from django.utils import timezone
from twofaclogin.models import Authorization


class Command(BaseCommand):
    help = 'Clean up expired authorization tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        # Get expired authorizations
        expired_auths = Authorization.objects.filter(expires__lt=timezone.now())
        count = expired_auths.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired authorizations found.')
            )
            return
            
        if options['dry_run']:
            self.stdout.write(
                f'Would delete {count} expired authorization(s):'
            )
            for auth in expired_auths:
                self.stdout.write(
                    f'  - User: {auth.user.username}, Expired: {auth.expires}'
                )
        else:
            # Delete expired authorizations
            expired_auths.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired authorization(s).'
                )
            )
