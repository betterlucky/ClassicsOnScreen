from django.urls import path, include
from django.contrib import admin

from . import views

urlpatterns = [
    path("", views.blog_index, name="blog_index"),
    path("show/<int:pk>/", views.blog_detail, name="blog_detail"),
    path('film/<str:film_name>/', views.blog_film, name='blog_film'),
    path('location/<str:location_name>/', views.blog_location, name='blog_location'),
]
# Add Django site authentication urls (for login, logout, password management)

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]
