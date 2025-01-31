from django.core.management.base import BaseCommand
from blog.tasks import check_show_expiry
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run all daily maintenance tasks'

    def handle(self, *args, **kwargs):
        logger.info('Running daily maintenance tasks')
        
        # Check for expiring shows
        check_show_expiry()
        
        # Future tasks can be added here:
        # clean_expired_votes()
        # update_completed_shows()
        # etc. 