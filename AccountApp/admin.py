from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Doctor, Patient, Specialty

# Register your models here.

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'license_number', 'phone')
    search_fields = ('specialties',)
    ordering = ('last_name',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone')
    search_fields = ('last_name', 'first_name', 'national_id')
    ordering = ('last_name',)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
    )