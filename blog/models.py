from django.db import models
from django.contrib.auth.models import AbstractUser

class SiteUser(AbstractUser):
    credits = models.IntegerField(blank=True, null=True, default=0)

class Film(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name

class Show(models.Model):
    body = models.TextField(blank=False)
    created_by = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    film = models.ForeignKey("Film", on_delete=models.CASCADE, related_name="shows", blank=False)
    location = models.ForeignKey("Location", on_delete=models.CASCADE, related_name="shows", blank=False)
    eventtime = models.DateTimeField(blank=False)

    class Meta:
        ordering = ['eventtime']

    def __str__(self):
        # Updated to provide a meaningful string representation
        return f"{self.film.name} at {self.location.name} on {self.eventtime.strftime('%Y-%m-%d %H:%M')}"

class Comment(models.Model):
    author = models.ForeignKey("SiteUser", on_delete=models.CASCADE)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.author.username} on '{self.show}'"
