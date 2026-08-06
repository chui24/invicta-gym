from django.contrib import admin
from .models import Cliente, Plan, Suscripcion, Pago, ConfiguracionSistema, Asistencia

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'telefono', 'correo')
    search_fields = ('nombre', 'cedula')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion_dias', 'tarifa')
    search_fields = ('nombre',)

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'plan', 'fecha_inscripcion', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'plan')
    search_fields = ('cliente__nombre', 'cliente__cedula')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('suscripcion', 'monto', 'metodo_pago', 'fecha_pago')
    list_filter = ('metodo_pago', 'fecha_pago')

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ('dias_gracia',)

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_hora_entrada')
    list_filter = ('fecha_hora_entrada',)
