from django.contrib import admin
from django.urls import path, include
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('films/', views.film_list, name='film_list'),
    path('create_screening/', views.create_screening, name='create_screening'),
    path('screening/<int:screening_id>/', views.screening_detail, name='screening_detail'),
    path('my_screenings/', views.my_screenings, name='my_screenings'),
    path('accounts/', include('django.contrib.auth.urls')),  # For authentication
]
