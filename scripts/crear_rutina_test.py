import os
import django
from datetime import timedelta
from django.utils import timezone

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gym.models import Cliente, Mesociclo, DiaRutina, EjercicioRutina, AsignacionCliente, Personal

def create_test_routine():
    print("Buscando a Jesus Machado...")
    cliente = Cliente.objects.filter(nombre__icontains="jesus machado").first()
    
    if not cliente:
        print("No se encontró a Jesus Machado. Creando usuario de prueba...")
        # Intentaremos crearlo si no existe para la prueba (con datos dummy)
        cliente = Cliente.objects.create(
            nombre="Jesus Machado",
            cedula="TEST-123456",
            telefono="0000000000",
            email="jesus.machado.test@test.com"
        )
        print("Cliente de prueba Jesus Machado creado.")
    else:
        print(f"Cliente encontrado: {cliente.nombre} ({cliente.cedula})")

    # Obtener el primer coach disponible, si hay
    coach = Personal.objects.filter(cargo_especialidad__icontains='coach').first()
    if not coach:
        coach = Personal.objects.first()

    print("Creando Mesociclo de 4 semanas...")
    mesociclo = Mesociclo.objects.create(
        nombre="Rutina de Prueba (Martes a Sábado)",
        duracion_semanas=4,
        coach=coach
    )

    print("Generando Días y Ejercicios...")
    # Días activos: Martes (1), Miércoles (2), Jueves (3), Viernes (4), Sábado (5)
    # Por lo tanto, 5 días de entrenamiento por semana.
    for semana in range(1, 5):
        for numero_dia in range(1, 6):
            enfoques = ["Pecho y Tríceps", "Espalda y Bíceps", "Piernas (Cuádriceps)", "Hombros y Abs", "Piernas (Femorales y Glúteos)"]
            dia = DiaRutina.objects.create(
                mesociclo=mesociclo,
                semana=semana,
                numero_dia=numero_dia,
                enfoque=enfoques[numero_dia - 1]
            )
            
            # Crear un par de ejercicios dummy para cada día
            EjercicioRutina.objects.create(
                dia_rutina=dia,
                nombre_ejercicio=f"Ejercicio Principal {numero_dia}",
                series="4",
                repeticiones="10-12",
                peso_asignado="Al fallo"
            )
            EjercicioRutina.objects.create(
                dia_rutina=dia,
                nombre_ejercicio=f"Ejercicio Secundario {numero_dia}",
                series="3",
                repeticiones="15",
                peso_asignado="Moderado"
            )

    print("Asignando Rutina al Cliente con dias_activos [1, 2, 3, 4, 5]...")
    # Establecemos fecha_inicio hace 3 días para ver que haya avanzado la rutina (O podemos poner hoy)
    # Lo pondremos a hoy para evitar confusiones de inasistencias en la primera validación
    fecha_inicio = timezone.localdate()
    
    # Limpiamos asignaciones previas si tiene para no chocar
    AsignacionCliente.objects.filter(cliente=cliente).delete()

    AsignacionCliente.objects.create(
        cliente=cliente,
        mesociclo=mesociclo,
        fecha_inicio=fecha_inicio,
        dias_activos=[1, 2, 3, 4, 5]
    )

    print("¡Rutina creada y asignada exitosamente a Jesus Machado!")

if __name__ == '__main__':
    create_test_routine()
