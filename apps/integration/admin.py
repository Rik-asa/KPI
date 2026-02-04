#apps/integration/admin.py

from django.contrib import admin
from .models import MisImportedVisit, MisImportedSpecialization, MisImportedPurpose, MisImportedDoctor, MisImportedMan

@admin.register(MisImportedDoctor)
class MisImportedDoctorAdmin(admin.ModelAdmin):
    list_display = ['keyid', 'docnamemis', 'specnamemis', 'depnamemis', 'imported_at']
    list_filter = ['specnamemis', 'depnamemis', 'imported_at']
    search_fields = ['docnamemis', 'specnamemis', 'depnamemis']
    readonly_fields = ['imported_at']

@admin.register(MisImportedMan)
class MisImportedManAdmin(admin.ModelAdmin):
    list_display = ['keyid', 'manidmis', 'text', 'imported_at']
    search_fields = ['text']
    readonly_fields = ['imported_at']

@admin.register(MisImportedSpecialization)
class MisImportedSpecializationAdmin(admin.ModelAdmin):
    list_display = ['keyid', 'keyidmis', 'code', 'text', 'tag', 'imported_at']
    list_filter = ['tag', 'imported_at']
    search_fields = ['code', 'text']
    readonly_fields = ['imported_at']

@admin.register(MisImportedPurpose)
class MisImportedPurposeAdmin(admin.ModelAdmin):
    list_display = ['keyid', 'keyidmis', 'code', 'text', 'tag', 'imported_at']
    list_filter = ['tag', 'imported_at']
    search_fields = ['code', 'text']
    readonly_fields = ['imported_at']

@admin.register(MisImportedVisit)
class MisImportedVisitAdmin(admin.ModelAdmin):
    list_display = [
        'keyid', 'keyidmis', 'num', 'dat', 'doctorname', 'depname', 
        'vistype', 'imported_at'
    ]
    list_filter = ['dat', 'depname', 'vistype', 'imported_at']
    search_fields = ['num', 'doctorname', 'depname', 'keyidmis']
    readonly_fields = ['imported_at']
    date_hierarchy = 'dat'