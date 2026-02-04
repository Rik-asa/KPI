#apps\kpi_calc\models.py

from django.db import models

class KpiResult(models.Model):
    calculation_date = models.DateField()                      # Дата расчета
    doctor = models.ForeignKey('integration.MisImportedDoctor'
                    , on_delete=models.CASCADE, null=True, blank=True)
    specialization = models.ForeignKey(
        'integration.MisImportedSpecialization'
                    , on_delete=models.CASCADE)
    plan_type = models.ForeignKey('integration.MisImportedPurpose'
                    , on_delete=models.CASCADE)
    actual_value = models.IntegerField()                       # Фактическое значение
    plan_value = models.IntegerField()                         # Плановое значение
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Процент выполнения
    period = models.CharField(max_length=7)                    # Год-месяц '2024-05'
    
    class Meta:
        app_label = 'kpi_calc'
        unique_together = ['calculation_date', 'doctor' ,'specialization', 'plan_type', 'period']

    def __str__(self):
        if self.doctor:
            return f"{self.doctor.docnamemis} - {self.plan_type.text} - {self.period}"
        else:
            return f"{self.specialization} - {self.plan_type.text} - {self.period}"
        
