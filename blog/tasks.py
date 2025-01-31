from django.utils import timezone
from datetime import timedelta
from .models import Show
import logging

logger = logging.getLogger(__name__)

def check_show_expiry():
    """
    Check for shows that should expire:
    - Status is 'inactive' or 'tbc'
    - Less than 2 weeks until show date
    - Not enough credits
    """
    two_weeks_from_now = timezone.now() + timedelta(weeks=2)
    
    # Get shows that might expire
    expiring_shows = Show.objects.filter(
        status__in=['inactive', 'tbc'],
        eventtime__lte=two_weeks_from_now
    )
    
    for show in expiring_shows:
        # Check if credits meet minimum threshold
        if show.credits < show.location.min_capacity:
            logger.info(f"Expiring show: {show.film.name} at {show.location.name}")
            show.mark_expired() 