from django.core.management.base import BaseCommand
from plans.models import KpiPlan
from integration.models import MisImportedSpecialization, MisImportedPurpose
from references.models import Specialization, PlanType

class Command(BaseCommand):
    help = 'Создание простых планов для расчета KPI'
    
    def handle(self, *args, **options):
        # Используем существующие Specialization и PlanType, но с данными из МИС
        # Или создаем минимальные если их нет
        
        # Создаем один план для демонстрации
        spec, _ = Specialization.objects.get_or_create(
            code='DEFAULT_SPEC',
            defaults={'name': 'Общая специальность', 'description': 'Для демонстрации'}
        )
        
        plan_type, _ = PlanType.objects.get_or_create(
            code='visits_total',
            defaults={'name': 'Общее количество визитов', 'formula_hint': 'P = Факт/План * 100%'}
        )
        
        # Создаем план
        plan, created = KpiPlan.objects.get_or_create(
            year=2025,
            specialization=spec,
            plan_type=plan_type,
            defaults={'plan_value': 100}  # План: 100 визитов
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Создан демонстрационный план: {spec.name} - {plan_type.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('ℹ️ Демонстрационный план уже существует')
            )