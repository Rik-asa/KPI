# apps/kpi_calc/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('plan-fact-comparison/', views.dynamic_plan_fact_view, name='plan_fact_comparison'),
]