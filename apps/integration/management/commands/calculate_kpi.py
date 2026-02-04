#apps\integration\management\commands\calculate_kpi.py

from django.core.management.base import BaseCommand
from kpi_calc.calculators import run_kpi_calculation

class Command(BaseCommand):
    help = 'Запуск расчета KPI показателей за указанный период'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            help='Период в формате YYYY-MM (например, 2025-04)',
        )
    
    def handle(self, *args, **options):
        period = options.get('period')
        
        self.stdout.write(f"Запуск расчета KPI за период: {period or 'предыдущий месяц'}...")
        
        try:
            results = run_kpi_calculation(period)
            
            if results:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Успешно рассчитано {len(results)} показателей KPI')
                )
            else:
                self.stdout.write(self.style.WARNING('⚠️ Нет данных для расчета KPI'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при расчете KPI: {e}')
            )