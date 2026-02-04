# apps/kpi_calc/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connection
from datetime import datetime
from integration.models import MisImportedDoctor, MisImportedSpecialization, MisImportedPurpose, MisImportedMan
from kpi_calc.models import KpiResult
from apps.core.db_utils import get_months_from_db, get_month_name

@login_required
def dynamic_plan_fact_view(request):
    """View с ДИНАМИЧЕСКИМИ колонками из структуры процедуры БД"""
    
    # Параметры из GET-запроса
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    # Значения по умолчанию
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    # Конвертируем типы
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    # Обработка опциональных параметров
    man_id = request.GET.get('man_id')
    specid = request.GET.get('specid')
    plan_vistype = request.GET.get('plan_vistype')
    
    # Преобразуем пустые строки в None
    man_id = int(man_id) if man_id and man_id.strip() else None
    specid = int(specid) if specid and specid.strip() else None
    plan_vistype = int(plan_vistype) if plan_vistype and plan_vistype.strip() else None
    
    columns = []
    data = []
    error_message = None
    
    try:
        with connection.cursor() as cursor:
            # Получаем структуру через LIMIT 0
            test_sql = """
            SELECT * FROM kpi.get_monthly_plan_fact_comparison(%s, %s, %s, %s, %s) LIMIT 0
            """
            test_params = [year, month, man_id, specid, plan_vistype]
            cursor.execute(test_sql, test_params)
            
            # Получаем колонки из description курсора
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                print(f"✅ Получены колонки из процедуры: {columns}")
            else:
                # Резервный - статический список
                columns = [
                    'Год', 'Месяц', 'Врач', 'Специальность', 'Тип_посещения',
                    'План_на_год', 'План_нарастающий_итог', 'Факт_нарастающий_итог',
                    'Процент_нарастающий_итог', 'План_за_месяц', 'Факт_за_месяц', 'Процент_за_месяц'
                ]
                print(f"⚠️ Используем статический список колонок: {columns}")
            
            # Получаем реальные данные
            data_sql = """
            SELECT * FROM kpi.get_monthly_plan_fact_comparison(%s, %s, %s, %s, %s)
            """
            cursor.execute(data_sql, test_params)
            results = cursor.fetchall()
            
            # Преобразуем в список словарей
            for row in results:
                row_dict = {}
                for i, value in enumerate(row):
                    col_name = columns[i] if i < len(columns) else f'col_{i}'
                    row_dict[col_name] = value
                data.append(row_dict)
            
            print(f"✅ Получено записей: {len(data)}")
            
    except Exception as e:
        error_message = str(e)
        print(f"❌ Ошибка: {error_message}")
        # В случае ошибки используем статический список
        columns = [
            'Год', 'Месяц', 'Врач', 'Специальность', 'Тип_посещения',
            'План_на_год', 'План_нарастающий_итог', 'Факт_нарастающий_итог',
            'Процент_нарастающий_итог', 'План_за_месяц', 'Факт_за_месяц', 'Процент_за_месяц'
        ]

    # ПОЛУЧАЕМ ДАННЫЕ ДЛЯ ВЫПАДАЮЩИХ СПИСКОВ
    doctors_data = []
    try:
        # Врачи (из import_man)
        
        man_users = MisImportedMan.objects.all().order_by('text')

        for man in MisImportedMan.objects.all().order_by('text'):
            if man.text and man.manidmis:
                doctors_data.append({
                    'id': man.manidmis,
                    'name': f"{man.text} (ID: {man.manidmis})"
                })
    except Exception as e:
        print(f"Ошибка при получении врачей: {e}")
        doctors_data = []
    
    try:
        # Специальности
        specializations_data = []
        for spec in MisImportedSpecialization.objects.all().order_by('text'):
            specializations_data.append({
                'id': spec.keyidmis,
                'name': f"{spec.text} (код: {spec.code})"
            })
    except Exception as e:
        print(f"Ошибка при получении специальностей: {e}")
        specializations_data = []
    
    try:
        # Цели визитов
        purposes_data = []
        for purpose in MisImportedPurpose.objects.all().order_by('text'):
            purposes_data.append({
                'id': purpose.code,
                'name': f"{purpose.text} (код: {purpose.code})"
            })
    except Exception as e:
        print(f"Ошибка при получении целей визитов: {e}")
        purposes_data = []
    
    # Подготавливаем значения для полей формы
    form_man_id = request.GET.get('man_id', '')
    form_specid = request.GET.get('specid', '')
    form_plan_vistype = request.GET.get('plan_vistype', '')
    
    is_doctor_user = not (request.user.is_accountant() or request.user.is_superuser)

    context = {
        'year': year,
        'month': month,
        'columns': columns,
        'data': data,
        'total': len(data),
        'error_message': error_message,
        'form_filters': {
            'man_id': form_man_id,
            'specid': form_specid,
            'plan_vistype': form_plan_vistype,
        },
        # Данные для выпадающих списков
        'doctors': doctors_data,
        'specializations': specializations_data,
        'purposes': purposes_data,
        'months': get_months_from_db(),
        'years': range(2025, datetime.now().year + 1),
        'is_doctor_user': is_doctor_user,
    }
    
    return render(request, 'kpi_calc/dynamic_comparison.html', context)