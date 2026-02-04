#apps\core\db_utils.py

"""
Утилиты для работы с БД, которые можно использовать ПОСЛЕ инициализации Django
"""

from django.db import connection

def get_months_from_db():
    """
    Получает список месяцев из таблицы kpi.months
    МОЖНО вызывать только после полной инициализации Django!
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT month_number, name 
            FROM kpi.months 
            ORDER BY month_number
        """)
        return cursor.fetchall()

def get_month_name(month_number):
    """Получает название месяца по номеру"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM kpi.months WHERE month_number = %s",
                [month_number]
            )
            result = cursor.fetchone()
            return result[0] if result else f"Месяц {month_number}"
    except Exception as e:
        # Если что-то пошло не так, возвращаем просто номер
        return f"Месяц {month_number}"