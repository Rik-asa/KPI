#kpi_core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.shortcuts import redirect
from django.contrib.auth import logout

from apps.dashboard.views import (
    dashboard_home, # главная для заведующих
    unified_plan_fact, # единая страница план-факт
    smart_redirect, # умный редирект
    doctor_dashboard  # если используется  дашборд врача
)

urlpatterns = [
    #администрирование
    path('admin/', admin.site.urls),

    # Аутентификация
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='dashboard/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='/accounts/login/'), name='logout'),

    # главные страницы
    path('', smart_redirect, name='home'),
    
    # дашборды
    path('dashboard/', include([
        # Главная страница для заведующих
        path('', dashboard_home, name='dashboard_home'),
        # Единая страница сравнения план-факт
        path('plan-fact/', unified_plan_fact, name='plan_fact'),
    ])),

    # API (только реально нужные)
    path('api/', include([
        path('users/', include('apps.users.urls')),
        # Другие API только если действительно используются
    ])),
    
    #path('api/users/', include('apps.users.urls')),
    #path('api/plans/', include('apps.plans.urls')),
    #path('api/kpi/', include('apps.kpi_calc.urls')),
    #path('api/dashboard/', include('apps.dashboard.urls')),
    #path('', include('apps.dashboard.urls')),  # Главная страница

    # Настройка БД
    path('setup/', include('setup.urls')),

    # Прямой путь для админки
    path('admin/setup/', lambda request: redirect('/setup/'), name='admin_database_setup'),
]