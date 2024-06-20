from django.db import models
from django.contrib.auth.models import User

class Film(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    poster_url = models.URLField()

class Screening(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    location = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='joined_screenings')

class Comment(models.Model):
    screening = models.ForeignKey(Screening, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
