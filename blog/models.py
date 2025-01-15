from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils.timezone import now


class SiteUser(AbstractUser):
    credits = models.IntegerField(blank=True, null=True, default=0)


class Film(models.Model):
    name = models.CharField(max_length=60, unique=True)
    overridecapacity = models.IntegerField(blank=True, null=True)
    imdb_code = models.CharField(max_length=10, blank=False, null=False, unique=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=60, unique=True)
    min_capacity = models.IntegerField(default=40, blank=False, null=False)

    def __str__(self):
        return self.name


class Show(models.Model):
    STATUS_CHOICES = [
        ('inactive', 'Inactive'),
        ('tbc', 'To Be Confirmed'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    body = models.TextField()
    created_by = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    film = models.ForeignKey("Film", on_delete=models.CASCADE, related_name="shows")
    location = models.ForeignKey("Location", on_delete=models.CASCADE, related_name="shows")
    eventtime = models.DateTimeField()
    credits = models.PositiveIntegerField(blank=True, null=True, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')

    subtitles = models.BooleanField(default=False, help_text="Does this show have subtitles?")
    relaxed_screening = models.BooleanField(default=False, help_text="Is this a relaxed screening?")

    class Meta:
        ordering = ['eventtime']
        unique_together = ('film', 'location', 'eventtime')

    def add_credits(self, user, amount):
        """Add credits to the show and update status if needed."""
        if amount <= 0:
            raise ValidationError("Credits must be a positive number.")
        if user.credits < amount:
            raise ValidationError("Insufficient credits.")

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

    def mark_completed(self):
        """Mark the show as completed."""
        if self.status == 'confirmed':
            self.status = 'completed'
            self.save()

    def cancel_show(self):
        """Cancel the show and refund credits."""
        if self.status in ['inactive', 'tbc']:
            self.refund_credits()
        self.status = 'cancelled'
        self.save()


    def clean(self):
        super().clean()

        # Check if the instance already exists in the database
        if not self.pk and self.eventtime < now() + timedelta(weeks=3):
            raise ValidationError("Shows cannot be created within three weeks of the current date.")


class ShowCreditLog(models.Model):
    user = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="credit_logs")
    credits = models.PositiveIntegerField()
    refunded = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']

class Comment(models.Model):
    author = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.author.username} on '{self.show}'"
