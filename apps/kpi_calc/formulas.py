#apps\kpi_calc\formulas.py
class KPIFormulas:
    @staticmethod
    def calculate_percentage(actual, plan):
        """P = Fakt/Plan * 100%"""
        if plan == 0:
            return 0
        return (actual / plan) * 100
    
    @staticmethod
    def calculate_validation_percentage(validated, total):
        """V = N_val/N_total * 100%"""
        return KPIFormulas.calculate_percentage(validated, total)
    
    @staticmethod
    def calculate_disease_percentage(total_visits, z_diagnosis_visits):
        """D = (N_total - N_z)/N_total * 100%"""
        disease_visits = total_visits - z_diagnosis_visits
        return KPIFormulas.calculate_percentage(disease_visits, total_visits)