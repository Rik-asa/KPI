# setup/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.setup_wizard, name='setup_wizard'),  # Это работает для /setup/ первого запуска
    path('test/', views.test_connection, name='test_connection'),  # /setup/test/
    path('save/', views.save_configuration, name='save_configuration'),  # /setup/save/
    path('admin/', views.admin_settings, name='admin_settings'),  # /setup/admin/
]