#apps\integration\management\commands\import_mis_references.py

from django.core.management.base import BaseCommand
from integration.mis_connector import MISConnector

class Command(BaseCommand):
    help = 'Импорт справочников (специальностей и целей) из МИС'
    
    def handle(self, *args, **options):
        connector = MISConnector()
        
        self.stdout.write("Проверка подключения к МИС...")
        if not connector.test_connection():
            self.stdout.write("❌ Нет подключения к МИС")
            return
        
        self.stdout.write("✅ Подключение к МИС успешно")
        
        # Импорт специальностей
        self.stdout.write("Выгрузка специальностей из МИС...")
        specializations_data = connector.extract_specializations()
        
        if specializations_data:
            self.stdout.write(f"Сохранение {len(specializations_data)} специальностей...")
            saved_count = connector.save_specializations_to_db(specializations_data)
            self.stdout.write(f"✅ Успешно импортировано {saved_count} специальностей")
        else:
            self.stdout.write("❌ Не удалось выгрузить специальности")
        
        # Импорт целей визитов
        self.stdout.write("Выгрузка целей визитов из МИС...")
        purposes_data = connector.extract_purposes()
        
        if purposes_data:
            self.stdout.write(f"Сохранение {len(purposes_data)} целей визитов...")
            saved_count = connector.save_purposes_to_db(purposes_data)
            self.stdout.write(f"✅ Успешно импортировано {saved_count} целей визитов")
        else:
            self.stdout.write("❌ Не удалось выгрузить цели визитов")