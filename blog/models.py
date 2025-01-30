from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.validators import RegexValidator
import requests
import re


class SiteUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds credit system functionality for show bookings.
    """
    credits = models.IntegerField(blank=True, null=True, default=0)

    def get_active_contributions(self):
        """Return all active show contributions."""
        return self.showcreditlog_set.filter(
            show__status__in=['tbc', 'confirmed'],
            refunded=False
        )


class Film(models.Model):
    """
    Represents a film that can be screened at various locations.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    overridecapacity = models.IntegerField(blank=True, null=True)
    imdb_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^tt\d{7,8}$',
                message='IMDB code must be in the format "tt" followed by 7-8 digits (e.g., tt0111161)',
            )
        ]
    )
    EDI_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Third party reference number for film booking"
    )

    class Meta:
        verbose_name = "Film"
        verbose_name_plural = "Films"

    def __str__(self):
        return self.name

    @property
    def upcoming_shows(self):
        """Get all upcoming shows for this film."""
        return self.shows.filter(
            eventtime__gt=now(),
            status__in=['tbc', 'confirmed']
        )

    def clean(self):
        if self.imdb_code:
            # Convert to lowercase and clean up URL if pasted
            self.imdb_code = self.imdb_code.lower()
            if 'imdb.com' in self.imdb_code:
                match = re.search(r'tt\d{7,8}', self.imdb_code)
                if match:
                    self.imdb_code = match.group(0)
                else:
                    raise ValidationError({
                        'imdb_code': 'Invalid IMDB code format. Please enter just the ID (e.g., tt0111161)'
                    })
            
            # Validate against OMDB API
            try:
                response = requests.get(
                    'http://www.omdbapi.com/',
                    params={
                        'i': self.imdb_code,
                        'apikey': settings.OMDB_API_KEY
                    }
                )
                data = response.json()
                
                if data.get('Response') == 'False':
                    raise ValidationError({
                        'imdb_code': 'Invalid IMDB code: Movie not found'
                    })
                
                # Compare movie title with our name (case-insensitive)
                imdb_title = data.get('Title', '').lower()
                our_title = self.name.lower()
                
                if not (imdb_title in our_title or our_title in imdb_title):
                    raise ValidationError({
                        'imdb_code': f'IMDB code is for "{data["Title"]}" but film name is "{self.name}"'
                    })
                
            except requests.RequestException as e:
                raise ValidationError({
                    'imdb_code': 'Could not validate IMDB code: Network error'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def has_active_shows(self):
        """Check if film has any active shows"""
        return self.upcoming_shows.filter(status__in=['tbc', 'confirmed']).exists()

    def deactivate(self):
        """
        Deactivate film if possible.
        Returns (success, message) tuple.
        """
        if self.has_active_shows():
            return False, f"Cannot remove '{self.name}' - has active shows"

        # Cancel all votes
        self.votes.all().delete()
        
        # Deactivate film
        self.active = False
        self.save()

        return True, f"Successfully removed '{self.name}'"


class VenueOwner(models.Model):
    """
    Represents a company or individual that owns one or more venues.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(
        verbose_name="Head Office Email",
        help_text="Primary contact email for the company"
    )

    class Meta:
        verbose_name = "Venue Owner"
        verbose_name_plural = "Venue Owners"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def active_locations(self):
        """Return all active locations owned by this company."""
        return self.locations.filter(active=True)


class Location(models.Model):
    """
    Represents a venue where shows can be screened.
    """
    name = models.CharField(max_length=60, unique=True)
    owner = models.ForeignKey(
        VenueOwner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations',
        help_text="The company or individual that owns this venue (optional for independent venues)"
    )
    contact_email = models.EmailField(
        verbose_name="Venue Manager Email",
        help_text="Direct contact email for the venue manager"
    )
    min_capacity = models.IntegerField(
        default=40,
        blank=False,
        null=False,
        help_text="Minimum number of credits required for show confirmation"
    )
    max_capacity = models.IntegerField(
        default=100,
        blank=False,
        null=False,
        help_text="Maximum number of credits allowed for this venue"
    )
    active = models.BooleanField(
        default=True,
        blank=False,
        help_text="Whether this venue is currently available for shows"
    )

    def clean(self):
        if self.max_capacity <= self.min_capacity:
            raise ValidationError({
                'max_capacity': 'Maximum capacity must be greater than minimum capacity'
            })

    def get_contact_emails(self):
        """
        Get all relevant contact emails for the venue.
        Returns both venue manager and owner emails if owner exists.
        """
        emails = [self.contact_email]
        if self.owner and self.owner.contact_email:
            emails.append(self.owner.contact_email)
        return list(set(emails))  # Remove any duplicates

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['name']

    def __str__(self):
        if self.owner:
            return f"{self.name} ({self.owner.name})"
        return self.name


class ShowOption(models.Model):
    """
    Represents different types of show options (e.g., Subtitles, Q&A, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(
        help_text="Explain what this option means for the show",
        blank=True
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether this option is currently available"
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Show Option"
        verbose_name_plural = "Show Options"

    def __str__(self):
        return self.name


class Show(models.Model):
    """
    Represents a movie screening event with credit-based booking system.
    
    The show goes through various states:
    - inactive: Initial state, accepting credits
    - tbc: Minimum credits reached, awaiting confirmation
    - confirmed: Show will proceed
    - completed: Show has occurred
    - cancelled: Show was cancelled
    - expired: Show didn't reach minimum credits
    """
    
    STATUS_CHOICES = [
        ('inactive', 'Inactive'),
        ('tbc', 'To Be Confirmed'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    body = models.TextField(help_text="Description and details about the show")
    created_by = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    film = models.ForeignKey("Film", on_delete=models.CASCADE, related_name="shows")
    location = models.ForeignKey("Location", on_delete=models.CASCADE, related_name="shows")
    eventtime = models.DateTimeField(help_text="Scheduled date and time of the show")
    credits = models.PositiveIntegerField(blank=True, null=True, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    options = models.ManyToManyField(
        ShowOption,
        blank=True,
        related_name='shows',
        help_text="Special features for this show"
    )

    class Meta:
        ordering = ['eventtime']
        unique_together = ('film', 'location', 'eventtime')
        verbose_name = "Show"
        verbose_name_plural = "Shows"

    def __str__(self):
        return f"{self.film.name} at {self.location.name} - {self.eventtime}"

    @property
    def is_active(self):
        """Check if the show is in an active state."""
        return self.status in ['tbc', 'confirmed']

    @property
    def total_credits(self):
        """Get total credits including refunded ones."""
        return self.credit_logs.aggregate(models.Sum('credits'))['credits__sum'] or 0

    @property
    def is_sold_out(self):
        """Check if the show has reached maximum capacity."""
        return self.credits >= self.location.max_capacity

    @property
    def can_add_credits(self):
        """Check if credits can be added to this show."""
        return (
            # Show must be inactive, tbc, or confirmed
            self.status in ['inactive', 'tbc', 'confirmed'] and
            # Show must not be sold out
            not self.is_sold_out and
            # Show must not have passed
            self.eventtime > timezone.now()
        )

    def can_transition_to(self, new_status):
        """Validate if the show can transition to the given status."""
        valid_transitions = {
            'inactive': ['tbc', 'cancelled', 'expired'],
            'tbc': ['confirmed', 'cancelled', 'expired'],
            'confirmed': ['completed', 'cancelled'],
            'completed': [],  # No transitions allowed from completed
            'cancelled': [],  # No transitions allowed from cancelled
            'expired': [],    # No transitions allowed from expired
        }
        return new_status in valid_transitions.get(self.status, [])

    def notify_credit_purchase(self):
        """Send email notifications to user who contributed credits."""
        subject = f"Credit Purchase Confirmation: {self.film.name}"
        
        message = render_to_string(
            'credit_purchase_email.html',
            {
                'user': self.credit_logs.last().user,  # Get the most recent credit log's user
                'show': self,
                'credits': self.credit_logs.last().credits,  # Get the number of credits from the most recent log
                'domain': settings.SITE_DOMAIN
            }
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.credit_logs.last().user.email],
            fail_silently=False,
        )

    def add_credits(self, user, amount):
        """Add credits to the show and update status if needed."""
        if amount <= 0:
            raise ValidationError("Credits must be a positive number.")
        if user.credits < amount:
            raise ValidationError(f"Insufficient credits. You have {user.credits} credits.")
        if self.credits + amount > self.location.max_capacity:
            remaining = self.location.max_capacity - self.credits
            raise ValidationError(
                f"This would exceed the venue's capacity. Maximum {remaining} credits can be added."
            )

        self.credits += amount
        user.credits -= amount
        user.save()

        # Log the contribution
        ShowCreditLog.objects.create(user=user, show=self, credits=amount)

        # Send purchase confirmation email
        self.notify_credit_purchase()

        # Update status to TBC if the threshold is met
        if self.credits >= self.location.min_capacity and self.status == 'inactive':
            self.status = 'tbc'
        self.save()

    def refund_credits(self, user=None):
        """
        Refund credits to users.
        If user is specified, refund only that user's credits.
        If no user is specified, refund all users (for show expiry/cancellation via admin).
        """
        if user:
            # Individual refund
            try:
                log = self.credit_logs.get(user=user, refunded=False)
                user.credits += log.credits
                user.save()
                
                # Mark log as refunded
                log.refunded = True
                log.save()
                
                # Update show's total credits
                self.credits -= log.credits
                self.save()
                
                return True
                
            except ShowCreditLog.DoesNotExist:
                return False
                
        else:
            # Group refund (for expired or cancelled shows via admin)
            if self.status in ['cancelled', 'expired']:
                for log in self.credit_logs.filter(refunded=False):
                    log.user.credits += log.credits
                    log.user.save()
                    
                    # Mark log as refunded
                    log.refunded = True
                    log.save()
                
                return True
                
            return False

    def confirm_show(self):
        """Mark the show as confirmed and notify contributors."""
        if self.status == 'tbc' or self.status == 'confirmed':  # Only allow confirmation from 'tbc' or 'confirmed' status
            self.status = 'confirmed'
            self.save()

            # Notify all contributors
            self.notify_contributors()

    def notify_contributors(self, resend=False):
        """Send email notifications to all users who contributed credits."""
        emailed_users = set()
        contributors = self.credit_logs.values_list('user__email', flat=True).distinct()
        subject = f"Show Confirmed: {self.film.name} at {self.location.name}"

        for user_email in contributors:
            if user_email in emailed_users:
                continue

            users = SiteUser.objects.filter(email=user_email)

            for user in users:
                message = render_to_string(
                    'show_confirmation_email.html',
                    {
                        'user': user,
                        'show': self,
                        'domain': settings.SITE_DOMAIN
                    }
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                emailed_users.add(user_email)

    def mark_completed(self):
        """Mark the show as completed."""
        if self.status == 'confirmed':
            self.status = 'completed'
            self.save()

    def cancel_show(self):
        """Cancel the show and refund credits if applicable."""
        if self.status in ['inactive', 'tbc', 'confirmed']:
            # Refund credits for cancelled shows
            self.refund_credits()

            # Mark the show as cancelled
            self.status = 'cancelled'
            self.save()

            # Send cancellation notification
            self.notify_cancellation(
                subject=f"Show Cancelled: {self.film.name} at {self.location.name}",
                template_name='show_cancellation_email.html'
            )

    def notify_cancellation(self, subject, template_name):
        """Send email notifications to all users who contributed credits."""
        emailed_users = set()
        contributors = self.credit_logs.values_list('user__email', flat=True).distinct()

        for user_email in contributors:
            if user_email in emailed_users:
                continue

            users = SiteUser.objects.filter(email=user_email)

            for user in users:
                message = render_to_string(
                    template_name,
                    {
                        'user': user,
                        'show': self,
                        'domain': settings.SITE_DOMAIN
                    }
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                emailed_users.add(user_email)

    def mark_expired(self):
        """Mark the show as expired if it hasn't been confirmed in time."""
        # Check if the show is in 'tbc' or already 'expired' status
        if self.status not in ['tbc', 'inactive']:
            return  # Only process shows that are in 'tbc' or 'inactive' status

        # Check if the show has passed its scheduled time and hasn't been confirmed
        
        # Refund credits as the show is considered expired
        self.refund_credits()

        # Mark the show as expired
        self.status = 'expired'
        self.save()

        # Send the expired show notification
        self.notify_cancellation(
            subject=f"Show Expired: {self.film.name} at {self.location.name}",
            template_name='show_expired_email.html'
        )

    def clean(self):
        """Validate show creation and updates."""
        super().clean()

        # Ensure eventtime is set before comparing
        

    @property
    def has_subtitles(self):
        """Check if this show has subtitles option."""
        return self.options.filter(name__iexact='Subtitles').exists()

    @property
    def is_relaxed_screening(self):
        """Check if this is a relaxed screening."""
        return self.options.filter(name__iexact='Relaxed').exists()


class ShowCreditLog(models.Model):
    """
    Tracks credit contributions to shows.
    """
    user = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="credit_logs")
    credits = models.PositiveIntegerField()
    refunded = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']
        verbose_name = "Show Credit Log"
        verbose_name_plural = "Show Credit Logs"

    def __str__(self):
        return f"{self.user.username} - {self.credits} credits for {self.show}"


class Comment(models.Model):
    """
    Represents user comments on shows.
    """
    author = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"{self.author.username} on '{self.show}'"


class FilmVote(models.Model):
    """
    Tracks user votes for films they want to keep available.
    """
    MAX_VOTES_PER_USER = 5  # Add this constant
    
    user = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    film = models.ForeignKey("Film", on_delete=models.CASCADE, related_name="votes")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'film')  # Prevent duplicate votes
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.user.username}'s vote for {self.film.name}"

    @property
    def days_remaining(self):
        """Returns number of days until vote expires"""
        from django.utils import timezone
        from datetime import timedelta
        
        expiry_date = self.created_on + timedelta(days=30)
        remaining = expiry_date - timezone.now()
        return max(0, remaining.days)

    @property
    def is_expired(self):
        """Check if vote has expired"""
        return self.days_remaining == 0


class FAQ(models.Model):
    """
    Stores Frequently Asked Questions and their answers.
    """
    CATEGORY_CHOICES = [
        ('general', 'General Questions'),
        ('tickets', 'Tickets and Booking'),
        ('other', 'Other Questions'),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'created_on']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
