#apps\integration\management\commands\import_mis_all_data.py

from django.core.management.base import BaseCommand
from integration.mis_connector import MISConnector

class Command(BaseCommand):
    help = 'Полный импорт всех данных из МИС'
    
    def handle(self, *args, **options):
        connector = MISConnector()
        
        self.stdout.write("=== ПОЛНЫЙ ИМПОРТ ДАННЫХ ИЗ МИС ===")
        
        # Проверка подключения
        if not connector.test_connection():
            self.stdout.write("❌ Нет подключения к МИС")
            return
        
        self.stdout.write("✅ Подключение к МИС успешно")
        
        # 1. Импорт пользователей
        self.stdout.write("\n1. Импорт пользователей...")
        man_data = connector.extract_man_users()
        if man_data:
            saved_count = connector.save_man_to_db(man_data)
            self.stdout.write(f"✅ Импортировано пользователей: {saved_count}")
        
        # 2. Импорт врачей
        self.stdout.write("\n2. Импорт врачей...")
        doctors_data = connector.extract_doctors()
        if doctors_data:
            saved_count = connector.save_doctors_to_db(doctors_data)
            self.stdout.write(f"✅ Импортировано врачей: {saved_count}")
        
        # 3. Импорт специальностей
        self.stdout.write("\n3. Импорт специальностей...")
        specializations_data = connector.extract_specializations()
        if specializations_data:
            saved_count = connector.save_specializations_to_db(specializations_data)
            self.stdout.write(f"✅ Импортировано специальностей: {saved_count}")
        
        # 4. Импорт целей визитов
        self.stdout.write("\n4. Импорт целей визитов...")
        purposes_data = connector.extract_purposes()
        if purposes_data:
            saved_count = connector.save_purposes_to_db(purposes_data)
            self.stdout.write(f"✅ Импортировано целей визитов: {saved_count}")
        
        self.stdout.write(
            self.style.SUCCESS("\n=== ИМПОРТ ЗАВЕРШЕН ===")
        )