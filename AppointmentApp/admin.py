from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'duration_minutes', 'status')
    search_fields = ('patient', 'doctor', 'appointment_date', 'status')
    list_filtrer = ('patient', 'doctor', 'status')
    ordering = ('appointment_date',)
    

# Register your models here.
