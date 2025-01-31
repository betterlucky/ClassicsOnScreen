from django.core.management.base import BaseCommand
from blog.tasks import check_show_expiry
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and expire shows that have not received enough credits'

    def handle(self, *args, **kwargs):
        logger.info('Starting expiry check command')
        try:
            check_show_expiry()
            self.stdout.write(self.style.SUCCESS('Show expiry check completed successfully'))
        except Exception as e:
            logger.error(f'Command failed: {str(e)}')
            self.stdout.write(self.style.ERROR('Show expiry check failed')) 