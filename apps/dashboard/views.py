# apps/dashboard/views.py

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.utils import timezone
from datetime import datetime
from integration.models import MisImportedDoctor, MisImportedSpecialization, MisImportedPurpose, MisImportedMan
from kpi_calc.views import dynamic_plan_fact_view
from apps.core.db_utils import get_months_from_db, get_month_name

@login_required
def dashboard_home(request):
    """Главная страница дашборда с редиректом в зависимости от роли."""
    
    # Если не заведующий и не админ - редирект на данные врача
    if not (request.user.is_accountant() or request.user.is_superuser):
        return redirect('unified_plan_fact')

    # Параметры из GET-запроса
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)

    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    # Получаем данные для диаграмм из PostgreSQL функций
    top_doctors = []
    specialization_stats = []
    
    # Получаем топ-5 врачей по выполнению плана
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    doctor_name,
                    specialization,
                    avg_percentage
                FROM kpi.get_top_doctors(%s, %s, 5)
            """
            cursor.execute(query, [year, month])
            results = cursor.fetchall()

            # Преобразуем результаты в список кортежей
            for row in results:
                # row = (doctor_name, specialization, avg_percentage)
                doctor_name = row[0] if row[0] else None
                specialization = row[1] if row[1] else None
                avg_percentage = float(row[2]) if row[2] is not None else 0.0
                top_doctors.append((doctor_name, specialization, avg_percentage))
                
    except Exception as e:
        print(f"Ошибка при получении топ-врачей: {e}")
        top_doctors = []

    # Получаем статистику по специальностям
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    specialization,
                    doctor_count,
                    avg_percentage,
                    total_plan,
                    total_fact
                FROM kpi.get_specialization_stats(%s, %s)
            """
            cursor.execute(query, [year, month])
            results = cursor.fetchall()

            for row in results:
                specialization = row[0] if row[0] else None
                doctor_count = row[1] if row[1] is not None else 0
                avg_percentage = float(row[2]) if row[2] is not None else 0.0
                total_plan = float(row[3]) if row[3] is not None else 0.0
                total_fact = row[4] if row[4] is not None else 0
                specialization_stats.append((specialization, doctor_count, avg_percentage, total_plan, total_fact))
                
    except Exception as e:
        print(f"Ошибка при получении статистики по специальностям: {e}")
        specialization_stats = []

    months_data = get_months_from_db()

    context = {
        'year': year,
        'month': month,
        'top_doctors': top_doctors,
        'specialization_stats': specialization_stats,
        'months': months_data,
        'years': range(2025, datetime.now().year + 1),
        'current_user': request.user,
    }
    
    return render(request, 'dashboard/accountant_dashboard.html', context)
    

@login_required
def doctor_dashboard(request):
    """Дашборд для врача с данными сравнения план-факт"""
    
    # Определяем текущего врача из данных пользователя
    man_id = request.user.manid if request.user.manid else None
    
    if not man_id:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'У вашего аккаунта не привязан ID врача из МИС'
        })

    # Получаем имя врача из таблицы man
    doctor_name = "Неизвестный врач"
    try:
        man = MisImportedMan.objects.filter(manidmis=man_id).first()
        if man and man.text:
            doctor_name = man.text
    except:
        pass

    # Параметры из GET-запроса
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)
    
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    columns = []
    data = []
    
    try:
        with connection.cursor() as cursor:
            # Используем процедуру сравнения план-факт с фильтром по врачу
            query = """
                SELECT * FROM kpi.get_monthly_plan_fact_comparison(%s, %s, %s, NULL, NULL)
            """
            cursor.execute(query, [year, month, man_id])
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                results = cursor.fetchall()
            
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        col_name = columns[i] if i < len(columns) else f'col_{i}'
                        row_dict[col_name] = value
                    data.append(row_dict)
    except Exception as e:
        print(f"Ошибка при получении данных план-факт: {e}")
    
    # Получаем данные для выпадающих списков
    doctors_data = []
    specializations_data = []
    purposes_data = []

    try:
        # Врачи
        for man in MisImportedMan.objects.all().order_by('text')[:50]:  # Ограничиваем
            if man.text and man.manidmis:
                doctors_data.append({
                    'id': man.manidmis,
                    'name': f"{man.text} (ID: {man.manidmis})"
                })
    except Exception as e:
        print(f"Ошибка при получении врачей: {e}")

    try:
        # Специальности
        for spec in MisImportedSpecialization.objects.all().order_by('text'):
            specializations_data.append({
                'id': spec.code,
                'name': f"{spec.text} (код: {spec.code})"
            })
    except Exception as e:
        print(f"Ошибка при получении специальностей: {e}")

    try:
        # Цели визитов
        for purpose in MisImportedPurpose.objects.all().order_by('text'):
            purposes_data.append({
                'id': purpose.code,
                'name': f"{purpose.text} (код: {purpose.code})"
            })
    except Exception as e:
        print(f"Ошибка при получении целей визитов: {e}")

    context = {
        'year': year,
        'month': month,
        'columns': columns,
        'data': data,
        'total': len(data),
        'doctor_id': man_id,
        'doctor_name': doctor_name,
        'is_doctor_dashboard': True,
        'form_filters': {
            'man_id': str(man_id),
            'specid': '',
            'plan_vistype': '',
        },
        # Данные для выпадающих списков
        'doctors': doctors_data,
        'specializations': specializations_data,
        'purposes': purposes_data,
        'months': get_months_from_db(),
        'years': range(2025, datetime.now().year + 1),
        'current_user': request.user,
        'is_doctor_user': True,  #флаг что это врач
    }
    
    return render(request, 'kpi_calc/dynamic_comparison.html', context)

def redirect_to_admin(request):
    """Редирект на стандартную админку Django."""
    return redirect('/admin/')


#умная фильтрация
@login_required
def unified_plan_fact(request):
    """
    ЕДИНАЯ страница сравнения план-факт.
    Рендерит dynamic_comparison.html напрямую.
    """
    user = request.user
    
    # Определяем роль
    is_manager = user.is_accountant() or user.is_superuser

    # ИНИЦИАЛИЗИРУЕМ переменные для всех случаев
    doctor_man_id = None
    doctor_name = ""
    
    # Для врача: получаем его данные
    if not is_manager:
        doctor_man_id = user.manid
        if not doctor_man_id:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'У вашего аккаунта не привязан ID врача из МИС'
            })
    
    # Параметры из GET (с умолчаниями)
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    year = request.GET.get('year', current_year)
    month = request.GET.get('month', current_month)
    
    # Конвертация
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = current_year
        month = current_month
    
    # ФИЛЬТРАЦИЯ ПО РОЛИ
    # Для врача: force его man_id
    # Для заведующего: из параметров или None
    if is_manager:
        man_id_param = request.GET.get('man_id', '').strip()
        man_id = int(man_id_param) if man_id_param else None
    else:
        man_id = doctor_man_id  # Автоматически для врача
    
    specid_param = request.GET.get('specid', '').strip()
    plan_vistype_param = request.GET.get('plan_vistype', '').strip()
    
    specid = int(specid_param) if specid_param else None
    plan_vistype = int(plan_vistype_param) if plan_vistype_param else None
    
    # Вызов хранимой процедуры
    columns = []
    data = []
    
    try:
        with connection.cursor() as cursor:
            query = "SELECT * FROM kpi.get_monthly_plan_fact_comparison(%s, %s, %s, %s, %s)"
            cursor.execute(query, [year, month, man_id, specid, plan_vistype])
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
            
            results = cursor.fetchall()
            
            # Преобразуем в словари
            for row in results:
                row_dict = {}
                for i, value in enumerate(row):
                    col_name = columns[i] if i < len(columns) else f'col_{i}'
                    row_dict[col_name] = value
                data.append(row_dict)
                
    except Exception as e:
        print(f"❌ Ошибка SQL: {e}")
    
    # ДАННЫЕ ДЛЯ ФИЛЬТРОВ (только нужное)
    doctors_data = []
    specializations_data = []
    purposes_data = []
    
    # Врачи: ТОЛЬКО для заведующих
    if is_manager:
        try:
            for man in MisImportedMan.objects.all().order_by('text')[:100]:
                if man.text and man.manidmis:
                    doctors_data.append({
                        'id': man.manidmis,
                        'name': f"{man.text}"
                    })
        except Exception:
            pass
    
    # Специальности: для всех
    try:
        for spec in MisImportedSpecialization.objects.all().order_by('text'):
            specializations_data.append({
                'id': spec.keyidmis,
                'name': spec.text
            })
    except Exception:
        pass
    
    # Цели: для всех
    try:
        for purpose in MisImportedPurpose.objects.all().order_by('text'):
            purposes_data.append({
                'id': purpose.code,
                'name': purpose.text
            })
    except Exception:
        pass
    
    # КОНТЕКСТ
    context = {
        # Основные данные
        'year': year,
        'month': month,
        'columns': columns,
        'data': data,
        'total': len(data),

        # Информация о пользователе
        'is_doctor_user': not is_manager,
        'current_user': user,

        # Если нужно передать имя врача для отображения
        'doctor_name': doctor_name if not is_manager else None,
        'doctor_id': doctor_man_id if not is_manager else None,
        

        # Фильтры
        'form_filters': {
            'man_id': str(man_id) if man_id else '',
            'specid': str(specid) if specid else '',
            'plan_vistype': str(plan_vistype) if plan_vistype else '',
        },

        # Фильтры
        'doctors': doctors_data,
        'specializations': specializations_data,
        'purposes': purposes_data,
        
        # Списки
        'months': get_months_from_db(),
        'years': range(2024, datetime.now().year + 2),
        
        # Заголовок страницы
        'page_title': 'Сравнение план-факт' if is_manager else 'Мои показатели',
    }
    
    return render(request, 'kpi_calc/dynamic_comparison.html', context)

def smart_redirect(request):
    """
    Умное перенаправление после логина или с главной.
    - Врачи → сразу на их данные
    - Заведующие → на общую статистику
    """
    if not request.user.is_authenticated:
        # Не авторизован → на логин
        from django.shortcuts import redirect
        return redirect('login')
    
    # Определяем куда отправлять
    if request.user.is_accountant() or request.user.is_superuser:
        # Заведующие/админы → на dashboard_home
        from django.shortcuts import redirect
        return redirect('dashboard_home')
    else:
        # Врачи → на единую страницу (их данные)
        from django.shortcuts import redirect
        return redirect('plan_fact')