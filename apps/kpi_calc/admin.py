#apps\kpi_calc\admin.py

from django.contrib import admin
from .models import KpiResult

@admin.register(KpiResult)
class KpiResultAdmin(admin.ModelAdmin):
    list_display = ['calculation_date',
                    'doctor',
                    'specialization',
                    'plan_type',
                    'actual_value',
                    'plan_value',
                    'percentage',
                    'period']
    list_filter = ['calculation_date',
                   'doctor',
                   'specialization',
                   'plan_type',
                   'period']
    search_fields = [
                    'doctor__docnamemis',
                    'specialization__text',
                    'plan_type__text', 
    ]