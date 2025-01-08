from django.urls import path, include
from django.contrib import admin

from . import views

urlpatterns = [
    path("", views.blog_index, name="blog_index"),
    path('register/', views.register, name='register'),
    path('confirm/<uidb64>/<token>/', views.activate, name='activate'),
    path('show/create/', views.create_show, name='create_show'),
    path("show/<int:pk>/", views.blog_detail, name="blog_detail"),
    path('film/<str:film_name>/', views.blog_film, name='blog_film'),
    path('location/<str:location_name>/', views.blog_location, name='blog_location'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('show/<int:show_id>/add-credits/', views.add_credits_to_show, name='add_credits_to_show'),
]
# Add Django site authentication urls (for login, logout, password management)

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]
