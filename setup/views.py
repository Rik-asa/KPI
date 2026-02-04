# setup/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from kpi_core.config import ConfigManager
import psycopg2
import json
from pathlib import Path
import secrets

def setup_wizard(request):
    """Мастер настройки"""
    from pathlib import Path
    env_file = Path(__file__).parent.parent / '.env'
    
    print(f"\n🔍 setup_wizard: .env существует = {env_file.exists()}")
    print(f"   Путь запроса: {request.path}")
    
    if env_file.exists() and env_file.stat().st_size > 0:
        print("✅ .env найден, перенаправляю на /")
        # Принудительно перезагружаем конфигурацию
        import importlib
        import sys
        if 'kpi_core.config' in sys.modules:
            importlib.reload(sys.modules['kpi_core.config'])
        
        return redirect('/')
    
    return render(request, 'setup/wizard.html')

@csrf_exempt
def test_connection(request):
    """Тестирование подключения к БД"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Только POST запросы'})
    
    db_type = request.POST.get('db_type')
    
    try:
        if db_type == 'kpi':
            conn = psycopg2.connect(
                dbname=request.POST.get('db_name'),
                user=request.POST.get('db_user'),
                password=request.POST.get('db_password'),
                host=request.POST.get('db_host'),
                port=request.POST.get('db_port', '5432')
            )
        else:  # mis
            conn = psycopg2.connect(
                dbname=request.POST.get('mis_name'),
                user=request.POST.get('mis_user'),
                password=request.POST.get('mis_password'),
                host=request.POST.get('mis_host'),
                port=request.POST.get('mis_port', '5432')
            )
        
        conn.close()
        return JsonResponse({'success': True, 'message': 'Подключение успешно'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def save_configuration(request):
    """Создает .env файл из данных мастера"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Только POST запросы'})
    
    try:
        # Генерируем безопасный SECRET_KEY
        secret_key = secrets.token_urlsafe(50)
        
        # Формируем содержимое .env
        env_content = f"""# ==== ОСНОВНАЯ БАЗА ДАННЫХ KPI ====
DB_NAME={request.POST.get('db_name')}
DB_USER={request.POST.get('db_user')}
DB_PASSWORD={request.POST.get('db_password')}
DB_HOST={request.POST.get('db_host', 'localhost')}
DB_PORT={request.POST.get('db_port', '5432')}

# ==== БАЗА ДАННЫХ МИС (опционально) ====
"""
        
        # Добавляем настройки МИС если есть
        mis_host = request.POST.get('mis_host', '')
        if mis_host:
            env_content += f"""MIS_DB_HOST={mis_host}
MIS_DB_NAME={request.POST.get('mis_name', '')}
MIS_DB_USER={request.POST.get('mis_user', '')}
MIS_DB_PASSWORD={request.POST.get('mis_password', '')}
MIS_DB_PORT={request.POST.get('mis_port', '5432')}

"""
        
        env_content += f"""# ==== НАСТРОЙКИ БЕЗОПАСНОСТИ DJANGO ====
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
"""
        
        # Записываем файл .env
        env_file = Path(__file__).parent.parent / '.env'
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ Файл .env создан с безопасным SECRET_KEY")
        
        return JsonResponse({
            'success': True, 
            'message': 'Настройки сохранены. Закройте и откройте страницу заново.',
            'redirect': '/'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@csrf_exempt
def admin_settings(request):
    """Страница настроек для администраторов (работает даже если .env существует)"""
    
    # Загружаем текущие настройки из .env
    settings = {}
    env_file = Path(__file__).parent.parent / '.env'
    
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        settings[key.strip()] = value.strip()
        except Exception as e:
            pass
    
    saved = False
    error = None
    
    if request.method == 'POST':
        
        try:
            # Получаем значения из формы
            
            form_data = {
                'DB_HOST': request.POST.get('db_host', 'localhost').strip(),
                'DB_PORT': request.POST.get('db_port', '5432').strip(),
                'DB_NAME': request.POST.get('db_name', 'kpi').strip(),
                'DB_USER': request.POST.get('db_user', 'postgres').strip(),
            }
            
            # Пароль KPI (обновляем только если введен новый)
            db_password = request.POST.get('db_password', '').strip()
            if db_password:
                form_data['DB_PASSWORD'] = db_password
            else:
                form_data['DB_PASSWORD'] = settings.get('DB_PASSWORD', '')
            
            # Настройки МИС
            mis_host = request.POST.get('mis_host', '').strip()
            
            form_data['MIS_DB_HOST'] = mis_host
            form_data['MIS_DB_PORT'] = request.POST.get('mis_port', '5432').strip()
            form_data['MIS_DB_NAME'] = request.POST.get('mis_name', '').strip()
            form_data['MIS_DB_USER'] = request.POST.get('mis_user', '').strip()
                        
            # Пароль МИС
            mis_password = request.POST.get('mis_password', '').strip()
            if mis_password:
                form_data['MIS_DB_PASSWORD'] = mis_password
            else:
                form_data['MIS_DB_PASSWORD'] = settings.get('MIS_DB_PASSWORD', '')
            
            # Сохраняем другие настройки
            form_data['DEBUG'] = settings.get('DEBUG', 'False')
            form_data['SECRET_KEY'] = settings.get('SECRET_KEY', '')
            form_data['ALLOWED_HOSTS'] = settings.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
            
            # Формируем содержимое .env
            env_content = []
            
            # Секция KPI БД
            env_content.append("# ==== ОСНОВНАЯ БАЗА ДАННЫХ KPI ====")
            env_content.append(f"DB_NAME={form_data['DB_NAME']}")
            env_content.append(f"DB_USER={form_data['DB_USER']}")
            env_content.append(f"DB_PASSWORD={form_data['DB_PASSWORD']}")
            env_content.append(f"DB_HOST={form_data['DB_HOST']}")
            env_content.append(f"DB_PORT={form_data['DB_PORT']}")
            env_content.append("")
            
            # Секция МИС БД - ВСЕГДА добавляем
            env_content.append("# ==== БАЗА ДАННЫХ МИС (опционально) ====")
            # Даже если хост пустой - сохраняем пустые значения
            env_content.append(f"MIS_DB_HOST={form_data['MIS_DB_HOST']}")
            env_content.append(f"MIS_DB_NAME={form_data['MIS_DB_NAME']}")
            env_content.append(f"MIS_DB_USER={form_data['MIS_DB_USER']}")
            env_content.append(f"MIS_DB_PASSWORD={form_data['MIS_DB_PASSWORD']}")
            env_content.append(f"MIS_DB_PORT={form_data['MIS_DB_PORT']}")
            env_content.append("")
            
            # Секция безопасности
            env_content.append("# ==== НАСТРОЙКИ БЕЗОПАСНОСТИ DJANGO ====")
            env_content.append(f"SECRET_KEY={form_data['SECRET_KEY']}")
            env_content.append(f"DEBUG={form_data['DEBUG']}")
            env_content.append(f"ALLOWED_HOSTS={form_data['ALLOWED_HOSTS']}")
            
            # Сохраняем файл
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            saved = True
            
            # Обновляем settings для отображения
            settings.update(form_data)
            
        except Exception as e:
            error = str(e)
    
    # Подготавливаем значения для формы
    defaults = {
        'db_host': settings.get('DB_HOST', 'localhost'),
        'db_port': settings.get('DB_PORT', '5432'),
        'db_name': settings.get('DB_NAME', 'kpi'),
        'db_user': settings.get('DB_USER', 'postgres'),
        'db_password': settings.get('DB_PASSWORD', ''),
        'mis_host': settings.get('MIS_DB_HOST', ''),
        'mis_port': settings.get('MIS_DB_PORT', '5432'),
        'mis_name': settings.get('MIS_DB_NAME', ''),
        'mis_user': settings.get('MIS_DB_USER', ''),
        'mis_password': settings.get('MIS_DB_PASSWORD', ''),
    }
    
    return render(request, 'setup/admin_settings.html', {
        'settings': defaults,
        'saved': saved,
        'error': error,
    })