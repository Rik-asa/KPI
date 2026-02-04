#apps\plans\admin.py

from django.contrib import admin
from django import forms
from .models import KpiPlan

class KpiPlanAdminForm(forms.ModelForm):
    """Форма с выпадающими списками"""
    
    class Meta:
        model = KpiPlan
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Заменяем виджеты для полей specid и plan_vistype
        self.fields['specid'].widget = forms.Select(choices=self.get_specialization_choices())
        self.fields['specid'].label = 'Специальность'
        
        self.fields['plan_vistype'].widget = forms.Select(choices=self.get_purpose_choices())
        self.fields['plan_vistype'].label = 'Цель визита'
    
    def get_specialization_choices(self):
        """Получаем choices для специальностей"""
        from integration.models import MisImportedSpecialization
        choices = [('', '--- Выберите специальность ---')]
        
        try:
            for spec in MisImportedSpecialization.objects.all().order_by('text'):
                # Преобразуем код в строку для choices
                choices.append((str(spec.keyidmis), spec.text))
        except Exception as e:
            print(f"Ошибка получения специальностей: {e}")
            
        return choices
    
    def get_purpose_choices(self):
        """Получаем choices для целей визитов"""
        from integration.models import MisImportedPurpose
        choices = [('', '--- Выберите цель визита ---')]
        
        try:
            for purpose in MisImportedPurpose.objects.all().order_by('text'):
                # Преобразуем код в строку для choices
                choices.append((str(purpose.code), purpose.text))
        except Exception as e:
            print(f"Ошибка получения целей визитов: {e}")
            
        return choices

class KpiPlanAdmin(admin.ModelAdmin):
    form = KpiPlanAdminForm
    list_display = ['year', 'specialization_name', 'purpose_name', 'plan_value', 'monthly_plan_display']
    list_filter = ['year']
    search_fields = ['specid', 'plan_vistype']
    
    def specialization_name(self, obj):
        return obj.get_specialization_name()
    specialization_name.short_description = 'Специальность'
    
    def purpose_name(self, obj):
        return obj.get_purpose_name()
    purpose_name.short_description = 'Цель визита'
    
    def monthly_plan_display(self, obj):
        return obj.monthly_plan()
    monthly_plan_display.short_description = 'План на месяц'

admin.site.register(KpiPlan, KpiPlanAdmin)