from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class SiteUser(AbstractUser):
    credits = models.IntegerField(blank=True, null=True, default=0)

class Film(models.Model):
    name = models.CharField(max_length=60, unique=True)
    overridecapacity = models.IntegerField(blank=True, null=True)

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
        ('TBC', 'To Be Confirmed'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
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

    class Meta:
        ordering = ['eventtime']
        unique_together = ('film', 'location', 'eventtime')

    def __str__(self):
        return f"{self.film.name} at {self.location.name} on {self.eventtime.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        if self.eventtime < now():
            raise ValidationError("Event time cannot be in the past.")

    def add_credits(self, user, amount):
        """Add credits to the show and update status if needed."""
        if amount <= 0:
            raise ValidationError("Credits must be a positive number.")
        self.credits += amount
        if self.credits >= self.location.min_capacity and self.status == 'inactive':
            self.status = 'tbc'
        self.save()

    def mark_completed(self):
        """Mark the show as completed if it has occurred."""
        if self.eventtime < now():
            self.status = 'completed'
            self.save()
        else:
            raise ValidationError("Cannot mark a future show as completed.")

class Comment(models.Model):
    author = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.author.username} on '{self.show}'"
