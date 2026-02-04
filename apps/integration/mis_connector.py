#apps/integration/mis_connector.py

import psycopg2
import os
from psycopg2 import sql
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connections
from .models import (MisImportedVisit, VisitAggregate
                     , MisImportedSpecialization, MisImportedPurpose
                     ,MisImportedDoctor, MisImportedMan)

class MISConnector:
    """Класс для подключения и выгрузки данных из МИС"""    
    
    def extract_recent_visits(self, days_back=1):
        """
        Выгрузка визитов из МИС за последние N дней
        Возвращает список визитов
        """
        try:
            # Рассчитываем дату начала выгрузки
            start_date = datetime.now() - timedelta(days=days_back)

            # SQL запрос для выгрузки данных из МИС
            query = """
            SELECT 
                v.keyid,           -- keyidmis
                v.num,             -- num
                v.casetypeid,
                v.dat,             -- dat
                v.dat1,            -- dat1  
                v.vistype,         -- vistype
                v.patientid,       -- patientid
                v.rootid,          -- rootidmis
                v.doctorid,        -- doctorid
                m.text as doctorname, -- ФИО врача
                d.depid,           -- depid
                dep.text as depname,  -- название отделения
                diag.code as diag_code, --код диагноза
                diag.text as diag_text,  --текст диагноза
                m.keyid as manid   -- manid
            FROM solution_med.visit v
            JOIN solution_med.docdep d ON v.doctorid = d.keyid
            JOIN solution_med.dep dep ON d.depid = dep.keyid  
            JOIN solution_med.doctor doc ON d.docid = doc.keyid
            JOIN solution_med.man m ON doc.man_id = m.keyid
            join solution_med.patdiag p on p.visitid = v.keyid
            join solution_med.diagnos diag on diag.keyid = p.diagid
            WHERE v.vistype BETWEEN 1 and 99
                AND v.casetypeid = 3746
                and p.diagtype = 1
                and v.dat is not null
                AND v.dat >= %s
            ORDER BY v.dat DESC
            """
            
            # Используем соединение из Django к БД МИС
            with connections['mis'].cursor() as cursor:
                cursor.execute(query, (start_date,))
                visits_data = cursor.fetchall()
            
            print(f"Выгружено {len(visits_data)} визитов из МИС")
            return visits_data
            
        except Exception as e:
            print(f"Ошибка при выгрузке из МИС: {e}")
            return []
    
    def save_visits_to_db(self, visits_data):
        """
        Сохраняет выгруженные данные в нашу БД
        """
        saved_count = 0
        
        for visit in visits_data:
            try:
                # Распаковываем данные согласно порядку в SELECT
                (keyid, num, casetypeid, dat, dat1, vistype, patientid,
                 rootid, doctorid, doctorname, depid, depname, diag_code, diag_text, manid) = visit
                
                # Создаем или обновляем запись
                obj, created = MisImportedVisit.objects.update_or_create(
                    keyidmis=keyid, # используем keyid из МИС как keyidmis
                    defaults={
                        'num': num or '',
                        'casetypeid': casetypeid,
                        'dat': dat,
                        'dat1': dat1,
                        'vistype': vistype,
                        'patientid': patientid,
                        'rootidmis': rootid,
                        'doctorid': doctorid,
                        'doctorname': doctorname or '',
                        'depid': depid,
                        'depname': depname or '',
                        'diag_code' : diag_code,
                        'diag_text' : diag_text,
                        'manid': manid,
                    }
                )
                
                if created:
                    saved_count += 1
                    
            except Exception as e:
                print(f"Ошибка при сохранении визита {keyid}: {e}")
                continue
        
        return saved_count
    
    def test_connection(self):
        """Проверка подключения к БД МИС"""
        try:
            with connections['mis'].cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Ошибка подключения к МИС: {e}")
            return False
        
    def extract_specializations(self):
        """Выгрузка справочника специальностей из МИС (tag = 9)"""
        try:
            query = """
                SELECT 
                    l.keyid,
                    l.tag,
                    l.code,
                    l.text
                FROM solution_med.lu l
                WHERE l.tag = 9  -- специальности врачей
                    AND l.status = 1
                ORDER BY l.code
            """
            
            with connections['mis'].cursor() as cursor:
                cursor.execute(query)
                specializations_data = cursor.fetchall()
            
            print(f"Выгружено {len(specializations_data)} специальностей из МИС")
            return specializations_data
            
        except Exception as e:
            print(f"Ошибка при выгрузке специальностей: {e}")
            return []
        
    def extract_purposes(self):
        """Выгрузка справочника целей визитов из МИС (tag = 20)"""
        try:
            query = """
                SELECT 
                    l.keyid,
                    l.tag,
                    l.code,
                    l.text
                FROM solution_med.lu l
                WHERE l.tag = 20  -- цели визитов
                    AND l.status = 1
                ORDER BY l.code
            """
            
            with connections['mis'].cursor() as cursor:
                cursor.execute(query)
                purposes_data = cursor.fetchall()
            
            print(f"Выгружено {len(purposes_data)} целей визитов из МИС")
            return purposes_data
            
        except Exception as e:
            print(f"Ошибка при выгрузке целей визитов: {e}")
            return []
        
    def save_specializations_to_db(self, specializations_data):
        """Сохраняет специальности в нашу БД"""
        saved_count = 0
        for spec in specializations_data:
            try:
                keyidmis, tag, code, text = spec
                
                obj, created = MisImportedSpecialization.objects.update_or_create(
                    keyidmis=keyidmis,
                    defaults={
                        'tag': tag,
                        'code': code,
                        'text': text or '',
                    }
                )
                if created:
                    saved_count += 1
            except Exception as e:
                print(f"Ошибка при сохранении специальности {keyidmis}: {e}")
                continue
        
        return saved_count
    
    def save_purposes_to_db(self, purposes_data):
        """Сохраняет цели визитов в нашу БД"""
        saved_count = 0
        for purpose in purposes_data:
            try:
                keyidmis, tag, code, text = purpose
                
                obj, created = MisImportedPurpose.objects.update_or_create(
                    keyidmis=keyidmis,
                    defaults={
                        'tag': tag,
                        'code': code,
                        'text': text or '',
                    }
                )
                if created:
                    saved_count += 1
            except Exception as e:
                print(f"Ошибка при сохранении цели {keyidmis}: {e}")
                continue
        
        return saved_count
    
    def extract_doctors(self):
        """Выгрузка врачей из МИС"""
        try:
            query = """
                SELECT 
                    d.keyid as keyiddocdep,
                    d.specid as specidmis,
                    s.text as specnamemis,
                    m.text as docnamemis,
                    d.depid as depidmis,
                    dep.text as depnamemis,
                    m.keyid as manidmis
                FROM solution_med.docdep d
                JOIN solution_med.lu s ON d.specid = s.keyid
                JOIN solution_med.doctor doc ON d.docid = doc.keyid
                JOIN solution_med.man m ON doc.man_id = m.keyid
                JOIN solution_med.dep dep ON d.depid = dep.keyid
                WHERE d.status = 1
            """
            
            with connections['mis'].cursor() as cursor:
                cursor.execute(query)
                doctors_data = cursor.fetchall()
            
            print(f"Выгружено {len(doctors_data)} врачей из МИС")
            return doctors_data
            
        except Exception as e:
            print(f"Ошибка при выгрузке врачей: {e}")
            return []

    def extract_man_users(self):
        """Выгрузка пользователей из МИС"""
        try:
            query = """
                SELECT 
                    m.keyid as manidmis,
                    m.text
                FROM solution_med.man m
                WHERE m.text IS NOT NULL
            """
        
            with connections['mis'].cursor() as cursor:
                cursor.execute(query)
                man_data = cursor.fetchall()
            
            print(f"Выгружено {len(man_data)} пользователей из МИС")
            return man_data
        
        except Exception as e:
            print(f"Ошибка при выгрузке пользователей: {e}")
            return []  

    def save_doctors_to_db(self, doctors_data):
        """Сохраняет врачей в нашу БД"""
        saved_count = 0
        for doctor in doctors_data:
            try:
                (keyiddocdep, specidmis, specnamemis, docnamemis, 
                depidmis, depnamemis, manidmis) = doctor
                
                obj, created = MisImportedDoctor.objects.update_or_create(
                    keyiddocdep=keyiddocdep,
                    defaults={
                        'specidmis': specidmis,
                        'specnamemis': specnamemis or '',
                        'docnamemis': docnamemis or '',
                        'depidmis': depidmis,
                        'depnamemis': depnamemis or '',
                        'manidmis': manidmis,
                    }
                )
                if created:
                    saved_count += 1
            except Exception as e:
                print(f"Ошибка при сохранении врача {keyiddocdep}: {e}")
                continue
        
        return saved_count
    
    def save_man_to_db(self, man_data):
        """Сохраняет пользователей в нашу БД"""
        saved_count = 0
        for man in man_data:
            try:
                manidmis, text = man
                
                obj, created = MisImportedMan.objects.update_or_create(
                    manidmis=manidmis,
                    defaults={
                        'text': text or '',
                    }
                )
                if created:
                    saved_count += 1
            except Exception as e:
                print(f"Ошибка при сохранении пользователя {manidmis}: {e}")
                continue
        
        return saved_count

# Функция для ручного запуска
def import_mis_data(days_back=1):
    """
    Основная функция для импорта данных из МИС
    days_back - за сколько дней выгружать данные
    """
    connector = MISConnector()
    
    print("Проверка подключения к МИС...")
    if not connector.test_connection():
        print("❌ Нет подключения к МИС")
        return
    
    print("✅ Подключение к МИС успешно")
    
    print(f"Выгрузка данных за последние {days_back} дней...")
    visits_data = connector.extract_recent_visits(days_back=days_back)
    
    if not visits_data:
        print("❌ Не удалось выгрузить данные из МИС")
        return
    
    print(f"Сохранение {len(visits_data)} визитов в нашу БД...")
    saved_count = connector.save_visits_to_db(visits_data)
    
    print(f"✅ Успешно импортировано {saved_count} записей")
    return saved_count