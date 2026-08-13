from django.contrib import admin
from .models import Cliente, Plan, Suscripcion, Pago, ConfiguracionSistema, Asistencia, Mesociclo, DiaRutina, EjercicioRutina, AsignacionCliente, RegistroProgresion

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

@admin.register(Mesociclo)
class MesocicloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion_semanas', 'coach')

@admin.register(DiaRutina)
class DiaRutinaAdmin(admin.ModelAdmin):
    list_display = ('mesociclo', 'numero_dia', 'enfoque')
    list_filter = ('mesociclo',)

@admin.register(EjercicioRutina)
class EjercicioRutinaAdmin(admin.ModelAdmin):
    list_display = ('nombre_ejercicio', 'dia_rutina', 'series', 'repeticiones')
    list_filter = ('dia_rutina__mesociclo', 'dia_rutina')

@admin.register(AsignacionCliente)
class AsignacionClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'mesociclo', 'fecha_inicio')
    search_fields = ('cliente__nombre',)

@admin.register(RegistroProgresion)
class RegistroProgresionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'ejercicio', 'peso_levantado', 'fecha')
    list_filter = ('fecha', 'cliente')
