#apps\integration\management\commands\import_mis_data.py

from django.core.management.base import BaseCommand
from integration.mis_connector import import_mis_data

class Command(BaseCommand):
    help = 'Импорт данных из МИС за последние N дней'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='За сколько дней выгружать данные (по умолчанию 1)',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        
        self.stdout.write(f"Запуск импорта данных из МИС за {days} дней...")
        
        result = import_mis_data(days_back=days)
        
        if result is not None:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Успешно импортировано {result} записей')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Импорт не удался')
            )