# apps/integration/tasks.py (для Celery)
from .mis_connector import import_mis_data

def sync_mis_data():
    """Задача для периодической синхронизации"""
    import_mis_data()