# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Пока оставьте пустым или добавьте базовые пути
    path('', views.user_list, name='user_list'),
]