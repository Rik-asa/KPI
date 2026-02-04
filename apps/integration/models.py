#apps/integration/models.py

from django.db import models

class MisImportedVisit(models.Model):
    keyid = models.BigAutoField(primary_key=True)     # наш авто-инкремент
    keyidmis = models.BigIntegerField(unique=True)    # уникальный ID из МИС
    num = models.BigIntegerField()
    casetypeid = models.IntegerField(null=True, blank=True)
    dat = models.DateTimeField()
    dat1 = models.DateTimeField(null=True, blank=True)
    vistype = models.IntegerField()
    patientid = models.BigIntegerField(null=True, blank=True)
    rootidmis = models.BigIntegerField(null=True, blank=True)  # родительский визит
    doctorid = models.BigIntegerField()
    doctorname = models.CharField(max_length=255)
    depid = models.BigIntegerField()
    depname = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    diag_code = models.CharField(max_length=12)
    diag_text = models.CharField(max_length=512)
    manid = models.BigIntegerField()
    
    class Meta:
        managed = False  # Django не будет управлять этой таблицей
        db_table = 'solution_med\".\"import_visit'  # Указываем схему и таблицу
        app_label = 'integration'

    def __str__(self):
        return f"{self.doctorname} - {self.dat}"
    
class VisitAggregate(models.Model):
    """Агрегированные данные по визитам для быстрого расчета KPI."""
    doctor_id = models.BigIntegerField()  # ID врача из МИС
    doctor_name = models.CharField(max_length=255)
    specialization = models.ForeignKey(
        'integration.MisImportedSpecialization'
        , on_delete=models.SET_NULL, null=True, blank=True)
    department_id = models.BigIntegerField()
    department_name = models.CharField(max_length=255)
    
    period = models.CharField(max_length=7)  # Формат 'YYYY-MM'
    
    total_visits = models.IntegerField(default=0)
    visits_by_purpose = models.JSONField(default=dict)  # {'vistype_code': count}
    validated_docs_count = models.IntegerField(default=0)
    total_docs_count = models.IntegerField(default=0)
    visits_with_z_diagnosis = models.IntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['doctor_id', 'period']
        verbose_name = 'Агрегированные визиты'
        verbose_name_plural = 'Агрегированные визиты'

    def __str__(self):
        return f"{self.doctor_name} - {self.period}"
    
class MisImportedSpecialization(models.Model):
    keyid = models.BigAutoField(primary_key=True)
    keyidmis = models.BigIntegerField(unique=True)  # ID из МИС
    tag = models.BigIntegerField()  # Номер справочника
    code = models.IntegerField()  # Код специальности
    text = models.CharField(max_length=255)  # Название специальности
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'kpi"."specialities'  # Указываем схему и таблицу

    def __str__(self):
        return f"{self.code} - {self.text}"

class MisImportedPurpose(models.Model):
    keyid = models.BigAutoField(primary_key=True)
    keyidmis = models.BigIntegerField(unique=True)  # ID из МИС
    tag = models.BigIntegerField()  # Номер справочника
    code = models.IntegerField()  # Код цели
    text = models.CharField(max_length=255)  # Название цели
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'kpi"."purposes'  # Указываем схему и таблицу

    def __str__(self):
        return f"{self.code} - {self.text}"
    
class MisImportedDoctor(models.Model):
    keyid = models.BigAutoField(primary_key=True)
    keyiddocdep = models.BigIntegerField(unique=True)  # ID из docdep
    specidmis = models.BigIntegerField()  # ID специальности из МИС
    specnamemis = models.CharField(max_length=1000)  # Название специальности
    docnamemis = models.CharField(max_length=1000)  # ФИО врача
    depidmis = models.BigIntegerField()  # ID отделения
    depnamemis = models.CharField(max_length=256)  # Название отделения
    manidmis = models.BigIntegerField()  # ID пользователя
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'solution_med"."import_doctor'

    def __str__(self):
        return self.docnamemis

class MisImportedMan(models.Model):
    keyid = models.BigAutoField(primary_key=True)
    manidmis = models.BigIntegerField(unique=True)  # ID пользователя из МИС
    text = models.CharField(max_length=256)  # ФИО пользователя
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'solution_med"."import_man'

    def __str__(self):
        return self.text