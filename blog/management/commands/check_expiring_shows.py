from django.core.management.base import BaseCommand
from blog.tasks import check_show_expiry
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and expire shows that have not received enough credits'

    def handle(self, *args, **kwargs):
        logger.info('Running show expiry check')
        check_show_expiry() 