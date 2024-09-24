from django.urls import path
from . import views

urlpatterns = [
    path('check-password/', views.check_password, name='check_password'),
    path('get-password-hint/', views.get_password_hint, name='get_password_hint'),
    path('verify-file/', views.verify_file, name='verify_file'),
    path('solar-system-data/', views.get_solar_system_data, name='get_solar_system_data'),    
]