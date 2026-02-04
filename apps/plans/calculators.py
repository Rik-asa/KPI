#apps\plans\calculators.py
class PlanCalculator:
    @staticmethod
    def get_annual_plan(year, specialization_id, plan_type_id):
        """Получить годовой план"""
        from .models import KpiPlan
        try:
            return KpiPlan.objects.get(
                year=year,
                specialization_id=specialization_id,
                plan_type_id=plan_type_id
            )
        except KpiPlan.DoesNotExist:
            return None