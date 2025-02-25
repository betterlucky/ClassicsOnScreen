from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('reset/', views.reset, name='reset'),
    path("", views.index, name="index"),
    path('register/', views.register, name='register'),
    path('confirm/<uidb64>/<token>/', views.activate, name='activate'),
    path('show/create/', views.create_show, name='create_show'),
    path("show/<int:pk>/", views.blog_detail, name="blog_detail"),
    path('film/<str:film_name>/', views.blog_film, name='blog_film'),
    path('location/<str:location_name>/', views.blog_location, name='blog_location'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('buy-credits/', views.buy_credits, name='buy_credits'),
    path('show/<int:show_id>/add-credits/', views.add_credits_to_show, name='add_credits_to_show'),
    path("about/", views.blog_about, name="blog_about"),
    path("faq/", views.blog_faq, name="blog_faq"),
    path("contact/", views.contact, name="contact"),
    path('accounts/', include('django.contrib.auth.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('refund-credits/<int:show_id>/', views.refund_credits_view, name='refund_credits'),
    path('films/', views.film_list, name='film_list'),
    path('films/most-desired/', views.most_desired_films, name='most_desired_films'),
    path('film/vote/<int:film_id>/', views.toggle_film_vote, name='toggle_film_vote'),
    path('validate/username/', views.validate_username, name='validate_username'),
    path('validate/email/', views.validate_email, name='validate_email'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# Add Django site authentication urls (for login, logout, password management)

