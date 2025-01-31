from django.utils import timezone
from datetime import timedelta
from .models import Show
import logging

# Set up logger
logger = logging.getLogger(__name__)

def check_show_expiry():
    """
    Check for shows that should expire:
    - Status is 'inactive' or 'tbc'
    - Less than 2 weeks until show date
    - Not enough credits
    """
    two_weeks_from_now = timezone.now() + timedelta(weeks=2)
    
    logger.info(f"Starting show expiry check at {timezone.now()}")
    
    try:
        # Get shows that might expire
        expiring_shows = Show.objects.filter(
            status__in=['inactive', 'tbc'],
            eventtime__lte=two_weeks_from_now
        )
        
        logger.info(f"Found {expiring_shows.count()} shows to check")
        
        expired_count = 0
        for show in expiring_shows:
            try:
                # Check if credits meet minimum threshold
                if show.credits < show.location.min_capacity:
                    logger.info(
                        f"Expiring show: {show.film.name} at {show.location.name} "
                        f"(Credits: {show.credits}/{show.location.min_capacity})"
                    )
                    show.mark_expired()
                    expired_count += 1
            except Exception as e:
                logger.error(f"Error processing show {show.id}: {str(e)}")
        
        logger.info(f"Completed show expiry check. Expired {expired_count} shows")
        
    except Exception as e:
        logger.error(f"Error during show expiry check: {str(e)}")
        raise 