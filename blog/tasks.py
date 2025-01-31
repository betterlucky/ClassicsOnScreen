from django.utils import timezone
from datetime import timedelta
from .models import Show
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def check_show_expiry():
    """
    Check for shows that should expire:
    - Status is 'inactive' or 'tbc'
    - Less than SHOW_EXPIRY_DAYS before show date
    - Not enough credits
    """
    expiry_threshold = timezone.now() + timedelta(days=settings.SHOW_EXPIRY_DAYS)
    
    # Get shows that might expire
    expiring_shows = Show.objects.filter(
        status__in=['inactive', 'tbc'],
        eventtime__lte=expiry_threshold
    )
    
    for show in expiring_shows:
        # Check if credits meet minimum threshold
        if show.credits < show.location.min_capacity:
            logger.info(f"Expiring show: {show.film.name} at {show.location.name}")
            show.mark_expired() 