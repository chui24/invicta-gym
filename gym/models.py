from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='clientes/', blank=True, null=True)
    descriptor_facial = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

class Plan(models.Model):
    nombre = models.CharField(max_length=100)
    duracion_dias = models.IntegerField(help_text="Duración del plan en días")
    tarifa = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} - {self.duracion_dias} días"

class Suscripcion(models.Model):
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Vencido', 'Vencido'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.RESTRICT)
    fecha_inscripcion = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')

    def save(self, *args, **kwargs):
        # Fechas dinámicas: Al crear o modificar, si no hay fecha de vencimiento, 
        # se calcula sumando la duración del plan a la fecha de inscripción.
        if not self.fecha_vencimiento and self.plan and self.fecha_inscripcion:
            self.fecha_vencimiento = self.fecha_inscripcion + timedelta(days=self.plan.duracion_dias)
        
        # Actualización automática del estado
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date():
            self.estado = 'Vencido'
        else:
            self.estado = 'Activo'
            
        super().save(*args, **kwargs)

    @property
    def dias_restantes(self):
        if not self.fecha_vencimiento:
            return 0
        delta = (self.fecha_vencimiento - timezone.now().date()).days
        return max(0, delta)

    @property
    def porcentaje_tiempo(self):
        if not self.fecha_vencimiento or not getattr(self, 'plan', None) or self.plan.duracion_dias <= 0:
            return 0
            
        ultimo_pago = self.pagos.order_by('-fecha_pago').first()
        inicio_ciclo = ultimo_pago.fecha_pago if ultimo_pago else self.fecha_inscripcion
        
        # Total de días desde el último pago hasta el vencimiento
        total_dias = (self.fecha_vencimiento - inicio_ciclo).days
        
        # Fallback de seguridad por si hay inconsistencias en fechas
        if total_dias <= 0:
            total_dias = self.plan.duracion_dias
            
        dias_rest = self.dias_restantes
        
        if dias_rest > total_dias:
            porcentaje_restante = 100
        else:
            porcentaje_restante = (dias_rest / total_dias) * 100
            
        return max(0, min(100, int(porcentaje_restante)))

    def __str__(self):
        return f"{self.cliente.nombre} - {self.plan.nombre}"

class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Pago Móvil', 'Pago Móvil'),
        ('Zelle', 'Zelle'),
        ('Punto de Venta', 'Punto de Venta'),
    ]

    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    fecha_pago = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Solo renovamos si es un pago subsiguiente (renovación), 
        # el primer pago (inscripción) ya tiene la fecha calculada en la vista/suscripción.
        if is_new:
            suscripcion = self.suscripcion
            if suscripcion.pagos.count() > 1:
                hoy = timezone.now().date()
                if suscripcion.fecha_vencimiento and suscripcion.fecha_vencimiento >= hoy:
                    suscripcion.fecha_vencimiento += timedelta(days=suscripcion.plan.duracion_dias)
                else:
                    suscripcion.fecha_vencimiento = hoy + timedelta(days=suscripcion.plan.duracion_dias)
                
                suscripcion.estado = 'Activo'
                suscripcion.save()

    def __str__(self):
        return f"Pago de {self.monto} - {self.suscripcion.cliente.nombre}"

class ConfiguracionSistema(models.Model):
    dias_gracia = models.IntegerField(default=0, help_text="Días de tolerancia después del vencimiento")
    tasa_bcv = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Tasa de cambio oficial BCV")
    ultima_actualizacion_bcv = models.DateTimeField(null=True, blank=True, help_text="Última vez que se actualizó la tasa")

    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracionSistema.objects.exists():
            # Patrón Singleton
            raise ValidationError('Solo puede existir una instancia de ConfiguracionSistema')
        return super(ConfiguracionSistema, self).save(*args, **kwargs)

    def __str__(self):
        return f"Configuración: {self.dias_gracia} días de gracia"

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1, defaults={'dias_gracia': 0})
        
        from django.utils import timezone
        
        hoy = timezone.now().date()
        ultima = config.ultima_actualizacion_bcv.date() if config.ultima_actualizacion_bcv else None
        
        if not ultima or ultima < hoy:
            from gym.utils.bcv_scraper import actualizar_tasa_bcv
            try:
                # Actualiza la tasa si no se ha hecho hoy
                nueva_tasa = actualizar_tasa_bcv()
                if nueva_tasa:
                    config.refresh_from_db()
            except Exception:
                pass
                
        return config

class Asistencia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='asistencias', null=True, blank=True)
    personal = models.ForeignKey('Personal', on_delete=models.CASCADE, related_name='asistencias', null=True, blank=True)
    fecha_hora_entrada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.cliente:
            return f"Asistencia Cliente: {self.cliente.nombre} - {self.fecha_hora_entrada.strftime('%Y-%m-%d %H:%M')}"
        elif self.personal:
            return f"Asistencia Equipo: {self.personal.nombre_completo} - {self.fecha_hora_entrada.strftime('%Y-%m-%d %H:%M')}"
        return f"Asistencia Desconocida - {self.fecha_hora_entrada.strftime('%Y-%m-%d %H:%M')}"

class Personal(models.Model):
    TURNO_CHOICES = [
        ('Mañana', 'Mañana'),
        ('Tarde', 'Tarde'),
        ('Noche', 'Noche'),
    ]
    
    CARGO_CHOICES = [
        ('Entrenadora', 'Entrenadora'),
        ('Entrenador', 'Entrenador'),
        ('Recepcionista', 'Recepcionista'),
        ('Gerencia', 'Gerencia'),
        ('Otro', 'Otro'),
    ]

    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nombre_completo = models.CharField(max_length=150)
    cargo_especialidad = models.CharField(max_length=50, choices=CARGO_CHOICES, default='Entrenadora')
    turno = models.CharField(max_length=20, choices=TURNO_CHOICES, default='Mañana')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='personal/', blank=True, null=True)
    descriptor_facial = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre_completo} - {self.cargo_especialidad}"

# --- FASE 3: RUTINAS Y PROGRESIÓN ---

class Mesociclo(models.Model):
    nombre = models.CharField(max_length=150)
    duracion_semanas = models.IntegerField(default=12)
    coach = models.ForeignKey(Personal, on_delete=models.SET_NULL, null=True, blank=True, related_name='mesociclos')
    
    def __str__(self):
        return f"{self.nombre} ({self.duracion_semanas} semanas)"

class DiaRutina(models.Model):
    mesociclo = models.ForeignKey(Mesociclo, on_delete=models.CASCADE, related_name='dias')
    semana = models.IntegerField(default=1)
    numero_dia = models.IntegerField()
    enfoque = models.CharField(max_length=150)
    
    class Meta:
        ordering = ['semana', 'numero_dia']
    
    def __str__(self):
        return f"Día {self.numero_dia}: {self.enfoque} - {self.mesociclo.nombre}"

class EjercicioRutina(models.Model):
    dia_rutina = models.ForeignKey(DiaRutina, on_delete=models.CASCADE, related_name='ejercicios')
    nombre_ejercicio = models.CharField(max_length=150)
    series = models.CharField(max_length=50)
    repeticiones = models.CharField(max_length=100)
    peso_asignado = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.nombre_ejercicio

class AsignacionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='asignaciones')
    mesociclo = models.ForeignKey(Mesociclo, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    dias_activos = models.JSONField(default=list, help_text="Días de la semana seleccionados para entrenar (0=Lunes, 6=Domingo)")
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.mesociclo.nombre}"

class RegistroProgresion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='progresiones')
    ejercicio = models.ForeignKey(EjercicioRutina, on_delete=models.CASCADE, related_name='registros')
    fecha = models.DateField(auto_now_add=True)
    peso_levantado = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.ejercicio.nombre_ejercicio}: {self.peso_levantado} ({self.fecha})"
