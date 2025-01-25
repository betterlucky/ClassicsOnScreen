from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


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
    name = models.CharField(max_length=60, unique=True)
    overridecapacity = models.IntegerField(blank=True, null=True)
    imdb_code = models.CharField(max_length=10, blank=False, null=False, unique=True)

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


class Location(models.Model):
    """
    Represents a venue where shows can be screened.
    """
    name = models.CharField(max_length=60, unique=True)
    min_capacity = models.IntegerField(
        default=40,
        blank=False,
        null=False,
        help_text="Minimum number of credits required for show confirmation"
    )

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

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

    subtitles = models.BooleanField(default=False, help_text="Do you want this show to have subtitles?")
    relaxed_screening = models.BooleanField(default=False, help_text="Will this be a relaxed screening?")

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

    def add_credits(self, user, amount):
        """Add credits to the show and update status if needed."""
        if amount <= 0:
            raise ValidationError("Credits must be a positive number.")
        if user.credits < amount:
            raise ValidationError(f"Insufficient credits. You have {user.credits} credits.")

        self.credits += amount
        user.credits -= amount
        user.save()

        # Log the contribution
        ShowCreditLog.objects.create(user=user, show=self, credits=amount)

        # Update status to TBC if the threshold is met
        if self.credits >= self.location.min_capacity and self.status == 'inactive':
            self.status = 'tbc'
        self.save()

    def refund_credits(self):
        """Refund credits to all users if the show expires."""
        if self.status not in ['inactive', 'tbc']:
            return  # Refund only applies to unconfirmed shows

        # Refund credits to users
        for log in self.credit_logs.all():
            log.user.credits += log.credits
            log.user.save()

            # Mark log as refunded instead of deleting it
            log.refunded = True
            log.save()

        # Update status to expired
        self.status = 'expired'
        self.save()

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
        if self.status in ['inactive', 'tbc']:
            self.refund_credits()
        self.status = 'cancelled'
        self.save()

    def clean(self):
        """Validate show creation and updates."""
        super().clean()

        # Validate event time
        if not self.pk and self.eventtime < now() + timedelta(weeks=3):
            raise ValidationError("Shows cannot be created within three weeks of the current date.")

        # Validate capacity
        if self.film.overridecapacity is not None and self.film.overridecapacity < 0:
            raise ValidationError("Override capacity cannot be negative")


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