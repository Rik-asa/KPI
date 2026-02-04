#apps\kpi_calc\calculators.py

from django.db import transaction
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime
import re

from integration.models import MisImportedVisit, VisitAggregate, MisImportedPurpose, MisImportedDoctor, MisImportedSpecialization, MisImportedPurpose
from references.models import Specialization, PlanType
from plans.models import KpiPlan
from .models import KpiResult

class KPICalculator:
    """Основной класс для расчета всех KPI показателей."""
    
    def __init__(self, period=None):
        """
        :param period: Период в формате 'YYYY-MM'. Если None, берется предыдущий месяц.
        """
        if period is None:
            now = timezone.now()
            self.period = now.replace(month=now.month-1).strftime('%Y-%m') if now.month > 1 else now.replace(year=now.year-1, month=12).strftime('%Y-%m')
        else:
            self.period = period
        
        self.year = int(self.period.split('-')[0])
    
    def calculate_percentage(self, actual, plan):
        """P = Fakt/Plan * 100%"""
        if plan == 0:
            return 0.0
        return round((actual / plan) * 100, 2)
    
    def calculate_validation_percentage(self, validated, total):
        """V = N_val/N_total * 100%"""
        return self.calculate_percentage(validated, total)
    
    def calculate_disease_percentage(self, total_visits, z_diagnosis_visits):
        """D = (N_total - N_z)/N_total * 100%"""
        disease_visits = total_visits - z_diagnosis_visits
        return self.calculate_percentage(disease_visits, total_visits)
    
    def is_z_diagnosis(self, diag_code):
        """Проверяет, относится ли диагноз к Z00-Z99 (МКБ-10)."""
        if not diag_code:
            return False
        # Простая проверка по префиксу 'Z'
        return diag_code.upper().startswith('Z')
    
    def aggregate_visits_data(self):
        """Агрегирует сырые данные из MisImportedVisit за период."""
        print(f"Агрегация данных за период: {self.period}")
        
        # Фильтруем визиты за нужный период
        year, month = map(int, self.period.split('-'))
        visits = MisImportedVisit.objects.filter(
            dat__year=year,
            dat__month=month
        )
        
        print(f"Найдено {visits.count()} визитов для агрегации.")
        
        # Группируем по врачам и агрегируем данные
        doctors_data = {}
        
        for visit in visits:
            doctor_key = visit.doctorid
            
            if doctor_key not in doctors_data:
                doctors_data[doctor_key] = {
                    'doctor_id': visit.doctorid,
                    'doctor_name': visit.doctorname,
                    'department_id': visit.depid,
                    'department_name': visit.depname,
                    'total_visits': 0,
                    'visits_by_purpose': {},
                    'validated_docs_count': 0,
                    'total_docs_count': 0,
                    'visits_with_z_diagnosis': 0,
                }
            
            data = doctors_data[doctor_key]
            data['total_visits'] += 1
            
            # Считаем визиты по цели (vistype)
            purpose_code = visit.vistype
            data['visits_by_purpose'][purpose_code] = data['visits_by_purpose'].get(purpose_code, 0) + 1
            
            # Считаем документы (упрощенно: считаем, что каждый визит = 1 документ)
            data['total_docs_count'] += 1
            # Критерий валидации: если визит завершен (casetypeid = 3746) и есть диагноз
            if visit.casetypeid == 3746 and visit.diag_code:
                data['validated_docs_count'] += 1
            
            # Считаем визиты с Z-диагнозами
            if self.is_z_diagnosis(visit.diag_code):
                data['visits_with_z_diagnosis'] += 1

        for doctor_key, data in list(doctors_data.items())[:3]:  # первые 3 врача
            print(f"📊 Врач {data['doctor_name']}:")
        
        return doctors_data
    
    def get_specialization_for_doctor(self, doctor_id, department_id):
        """Определяет специальность врача на основе реальных данных МИС."""

        try:
            # Ищем врача в импортированных данных
            doctor = MisImportedDoctor.objects.filter(keyiddocdep=doctor_id).first()
            
            if doctor:
                print(f"  Найден врач: {doctor.docnamemis}, специальность МИС: {doctor.specnamemis}")
                
                # Пытаемся найти соответствующую специальность в справочнике
                # specidmis - это ID специальности из таблицы lu в МИС
                mis_specialization = MisImportedSpecialization.objects.filter(
                    keyidmis=doctor.specidmis
                ).first()
                
                if mis_specialization:
                    print(f"  Найдена специальность: {mis_specialization.text}")
                    return mis_specialization
                else:
                    print(f"  ⚠️ Специальность с ID {doctor.specidmis} не найдена в справочнике")
            
            return None
            
        except Exception as e:
            print(f"  ❌ Ошибка при определении специальности для врача {doctor_id}: {e}")
            return None
    
    @transaction.atomic
    def calculate_all_kpi(self):
        """Основной метод: агрегирует данные и рассчитывает все KPI."""
        print(f"Запуск расчета KPI за {self.period}...")
        
        # 1. Агрегируем данные по визитам
        doctors_data = self.aggregate_visits_data()
        
        if not doctors_data:
            print("Нет данных для расчета.")
            return
        
        kpi_results = []
        doctors_without_plans = []
        
        for doctor_key, data in doctors_data.items():
            print(f"Обработка врача: {data['doctor_name']}")
            
            # 2. Определяем специальность врача
            mis_specialization = self.get_specialization_for_doctor(
                data['doctor_id'], 
                data['department_id']
            )
            
            if not mis_specialization:
                print(f"⚠️ Не найдена специальность для врача {data['doctor_name']}. Пропускаем.")
                continue

            #Находим объект врача для сохранения в KpiResult
            doctor_obj = MisImportedDoctor.objects.filter(keyiddocdep=data['doctor_id']).first()
            
            # 3. Сохраняем агрегированные данные
            aggregate, created = VisitAggregate.objects.update_or_create(
                doctor_id=data['doctor_id'],
                period=self.period,
                defaults={
                    'doctor_name': data['doctor_name'],
                    'specialization': mis_specialization,
                    'department_id': data['department_id'],
                    'department_name': data['department_name'],
                    'total_visits': data['total_visits'],
                    'visits_by_purpose': data['visits_by_purpose'],
                    'validated_docs_count': data['validated_docs_count'],
                    'total_docs_count': data['total_docs_count'],
                    'visits_with_z_diagnosis': data['visits_with_z_diagnosis'],
                }
            )
            
            # 4. Рассчитываем KPI для каждого типа плана
            purposes = MisImportedPurpose.objects.all()
            doctor_has_plans = False
            
            for purpose in purposes:
                try:
                    # Получаем годовой план для специальности и типа показателя
                    annual_plan = KpiPlan.objects.get(
                        year=self.year,
                        specid=mis_specialization.keyidmis,
                        plan_vistype=purpose.code
                    )
                    doctor_has_plans = True
                    
                    actual_value = data['visits_by_purpose'].get(purpose.code, 0)
                    plan_value = annual_plan.monthly_plan()
                    percentage = self.calculate_percentage(actual_value, plan_value)

                     # Логирование для отладки
                    #print(f" 🔍 РАСЧЕТ ДЛЯ '{purpose.text}':")
                    #print(f"    - Код цели: {purpose.code}")
                    #print(f"    - Визиты для этой цели: {actual_value}")
                    #print(f"    - Годовой план: {annual_plan.plan_value}")
                    #print(f"    - Месячный план: {plan_value}")
                    #print(f"    - Процент выполнения: {percentage}%")
                    
                    #сохранение в базу
                    #print(f" 🎯 СОХРАНЕНИЕ В БАЗУ:")
                    #print(f"    - actual_value для сохранения: {actual_value}")
                    #print(f"    - plan_value для сохранения: {plan_value}")
                    #print(f"    - percentage для сохранения: {percentage}")

                    # Создаем KPI результат
                    kpi_result, created = KpiResult.objects.update_or_create(
                        calculation_date=timezone.now().date(),
                        doctor=doctor_obj,
                        specialization=mis_specialization,
                        plan_type=purpose,
                        period=self.period,
                        defaults={
                            'actual_value': actual_value,
                            'plan_value': plan_value,
                            'percentage': percentage,
                        }
                    )
                    
                    #что сохранено
                    #print(f" ✅ СОХРАНЕНО В БАЗУ:")
                    #print(f"    - actual_value в базе: {kpi_result.actual_value}")
                    #print(f"    - plan_value в базе: {kpi_result.plan_value}")
                    #print(f"    - percentage в базе: {kpi_result.percentage}")

                    kpi_results.append(kpi_result)
                    
                    print(f"  ✅ Рассчитан {purpose.text}: {percentage}%")
                    
                except KpiPlan.DoesNotExist:
                    print(f" ⚠️ Не найден план для {mis_specialization.text} (код: {mis_specialization.code}) - цель {purpose.code} ({purpose.text})")
                    continue
                except Exception as e:
                    print(f"  ❌ Ошибка расчета {purpose.code}: {e}")
                    continue

            if not doctor_has_plans:
                print(f" ⚠️ Нет планов для врача {data['doctor_name']} ({mis_specialization.text})")

        print(f"✅ Расчет KPI завершен. Обработано результатов: {len(kpi_results)}")
        return kpi_results

# Утилитная функция для ручного запуска
def run_kpi_calculation(period=None):
    """Запускает расчет KPI для указанного периода."""
    calculator = KPICalculator(period)
    return calculator.calculate_all_kpi()