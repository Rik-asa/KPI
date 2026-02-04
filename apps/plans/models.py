#apps\plans\models.py

from django.db import models

class KpiPlan(models.Model):
    keyid = models.BigAutoField(primary_key=True)
    specid = models.IntegerField(verbose_name='Специальность')
    plan_vistype = models.IntegerField(verbose_name='Цель визита')
    plan_value = models.IntegerField(verbose_name='Плановое значение')
    year = models.IntegerField(verbose_name='Год')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'kpi"."plans'
        unique_together = ['year', 'specid', 'plan_vistype']

    def __str__(self):
        return f"{self.year}: {self.get_specialization_name()} - {self.get_purpose_name()} - {self.plan_value}"

    def get_specialization_name(self):
        """Получает название специальности по specid"""
        from integration.models import MisImportedSpecialization
        try:
            spec = MisImportedSpecialization.objects.get(keyidmis=self.specid)
            return spec.text
        except MisImportedSpecialization.DoesNotExist:
            return f"Специальность {self.specid}"

    def get_purpose_name(self):
        """Получает название цели визита по plan_vistype"""
        from integration.models import MisImportedPurpose
        try:
            purpose = MisImportedPurpose.objects.get(code=self.plan_vistype)
            return purpose.text
        except MisImportedPurpose.DoesNotExist:
            return f"Цель {self.plan_vistype}"

    def monthly_plan(self):
        """Расчет месячного плана"""
        import math
        return math.floor(self.plan_value / 12)

    @classmethod
    def get_specialization_choices(cls):
        """Возвращает choices для специальностей"""
        from integration.models import MisImportedSpecialization
        choices = []
        for spec in MisImportedSpecialization.objects.all().order_by('text'):
            choices.append((spec.code, spec.text))
        return choices

    @classmethod
    def get_purpose_choices(cls):
        """Возвращает choices для целей визитов"""
        from integration.models import MisImportedPurpose
        choices = []
        for purpose in MisImportedPurpose.objects.all().order_by('text'):
            choices.append((purpose.code, purpose.text))
        return choices