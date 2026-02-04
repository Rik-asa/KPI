#apps\kpi_calc\apps.py

from django.apps import AppConfig

class KpiCalcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kpi_calc'
    verbose_name = 'Расчет KPI'