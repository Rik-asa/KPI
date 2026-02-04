# kpi_core/config.py

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

class ConfigManager:
    """Менеджер конфигураций"""
    
    @staticmethod
    def is_configured():
        """Проверяет, настроена ли система"""
        env_file = Path(__file__).resolve().parent.parent / '.env'
        return env_file.exists() and env_file.stat().st_size > 0
    
    @staticmethod
    def get_django_databases():
        """Возвращает настройки БД для Django из .env"""
        if not ConfigManager.is_configured():
            raise ImproperlyConfigured(
                "Система не настроена. Создайте файл .env в корне проекта."
            )
        
        # Читаем .env файл
        env_file = Path(__file__).resolve().parent.parent / '.env'
        
        # Простой парсинг .env
        config = {}
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        databases = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config.get('DB_NAME', 'kpi'),
                'USER': config.get('DB_USER', 'postgres'),
                'PASSWORD': config.get('DB_PASSWORD', ''),
                'HOST': config.get('DB_HOST', 'localhost'),
                'PORT': config.get('DB_PORT', '5432'),
                'OPTIONS': {
                    'connect_timeout': 10,
                }
            }
        }
        
        # БД МИС (опционально)
        mis_host = config.get('MIS_DB_HOST')
        if mis_host:
            databases['mis'] = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config.get('MIS_DB_NAME', ''),
                'USER': config.get('MIS_DB_USER', ''),
                'PASSWORD': config.get('MIS_DB_PASSWORD', ''),
                'HOST': mis_host,
                'PORT': config.get('MIS_DB_PORT', '5432'),
            }
        
        return databases