from django.urls import path
from . import views

app_name = 'driverapp'

urlpatterns = [
    path('dashboard/', views.driver_dashboard, name='dashboard'),
    path('profile/', views.driver_profile, name='profile'),
    path('request_details/', views.request_details, name='request_details'),
]
