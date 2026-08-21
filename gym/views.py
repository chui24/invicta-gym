import base64
import json
import numpy as np
import cv2
import face_recognition
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, Q

from .models import Cliente, Asistencia, ConfiguracionSistema, Suscripcion, Pago, Plan, Personal, Mesociclo, DiaRutina, EjercicioRutina, AsignacionCliente, RegistroProgresion
from .forms import RegistroClienteForm, RenovacionForm, ClienteEditForm, PlanForm, PersonalForm

def get_face_encoding_from_base64(imgstr):
    try:
        # Decodificar imagen de base64 a un array numpy para opencv/face_recognition
        img_data = base64.b64decode(imgstr)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convertir a RGB ya que face_recognition espera RGB y cv2 decodifica a BGR
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Obtener los encodings
        encodings = face_recognition.face_encodings(rgb_img)
        if encodings:
            return encodings[0].tolist() # Devolver el primer rostro encontrado como lista
    except Exception as e:
        print(f"Error procesando imagen para encoding: {e}")
    return None

def validar_acceso_semaforo(request):
    """
    Vista (API) que recibe la cédula y devuelve el estado del cliente.
    """
    cedula = request.GET.get('cedula') or request.POST.get('cedula')
    
    if not cedula:
        return JsonResponse({'error': 'Cédula no proporcionada', 'estado': 'Rojo'}, status=400)
        
    try:
        cliente = Cliente.objects.get(cedula=cedula)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado', 'estado': 'Rojo'}, status=404)
        
    # Obtener la última suscripción
    suscripcion = cliente.suscripciones.order_by('-fecha_vencimiento').first()
    
    if not suscripcion or not suscripcion.fecha_vencimiento:
        return JsonResponse({
            'status': 'success',
            'tipo': 'cliente',
            'error': 'El cliente no tiene suscripciones activas', 
            'estado_color': 'Rojo',
            'estado': 'Inactivo',
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'cedula': cliente.cedula,
                'foto': cliente.foto_perfil.url if cliente.foto_perfil else None
            }
        })
        
    hoy = timezone.now().date()
    vencimiento = suscripcion.fecha_vencimiento
    
    # Obtener configuración de días de gracia
    config = ConfiguracionSistema.get_config()
    dias_gracia = config.dias_gracia
    
    limite_gracia = vencimiento + timedelta(days=dias_gracia)
    
    # Lógica del Semáforo
    if hoy <= vencimiento:
        if (vencimiento - hoy).days <= 3:
            estado_color = 'Amarillo'
            estado = 'Por vencer'
            mensaje = f'Acceso Permitido. Recuerde que su plan vence en {(vencimiento - hoy).days} días.'
        else:
            estado_color = 'Verde'
            estado = 'Activo'
            mensaje = 'Acceso Permitido'
        registrar_asistencia = True
    elif hoy <= limite_gracia:
        estado_color = 'Amarillo'
        estado = 'Por vencer'
        mensaje = f'Alerta: Mensualidad vencida. En periodo de gracia ({dias_gracia} días).'
        registrar_asistencia = True
    else:
        estado_color = 'Rojo'
        estado = 'Inactivo'
        mensaje = 'Acceso Denegado: Superó los días de gracia, exige pago.'
        registrar_asistencia = False
        
    if registrar_asistencia:
        Asistencia.objects.create(cliente=cliente)
        
    ultimo_pago = suscripcion.pagos.order_by('-fecha_pago').first()
    metodo_pago_usual = ultimo_pago.metodo_pago if ultimo_pago else 'No registrado'
    
    # --- LÓGICA DE RUTINA Y ALERTA DE INASISTENCIA ---
    rutina_dia_str = ""
    alerta_rutina_perdida = False
    dia_perdido_nombre = ""
    
    asignacion = AsignacionCliente.objects.filter(cliente=cliente).order_by('-fecha_inicio').first()
    if asignacion and asignacion.dias_activos:
        dias_activos = asignacion.dias_activos
        dia_semana_hoy = hoy.weekday() # 0 = Lunes, 6 = Domingo
        
        # 1. Determinar si hoy le toca
        if dia_semana_hoy in dias_activos:
            dias_transcurridos = (hoy - asignacion.fecha_inicio).days
            if dias_transcurridos >= 0:
                dias_entrenamiento_pasados = 0
                for i in range(dias_transcurridos):
                    d = asignacion.fecha_inicio + timedelta(days=i)
                    if d.weekday() in dias_activos:
                        dias_entrenamiento_pasados += 1
                        
                dia_rutina = dias_entrenamiento_pasados + 1
                total_dias_mesociclo = asignacion.mesociclo.dias.count()
                
                if dia_rutina <= total_dias_mesociclo:
                    rutina_dia_str = f"Rutina Día {dia_rutina}"
                else:
                    rutina_dia_str = "Mesociclo Completado"
        
        # 2. Alerta de Inasistencia (Lookback)
        fecha_lookback = hoy - timedelta(days=1)
        ultimo_dia_entrenamiento = None
        
        for _ in range(7):
            if fecha_lookback < asignacion.fecha_inicio:
                break
            if fecha_lookback.weekday() in dias_activos:
                ultimo_dia_entrenamiento = fecha_lookback
                break
            fecha_lookback -= timedelta(days=1)
            
        if ultimo_dia_entrenamiento:
            asistencia_previa = Asistencia.objects.filter(
                cliente=cliente, 
                fecha_hora_entrada__date=ultimo_dia_entrenamiento
            ).exists()
            
            if not asistencia_previa:
                alerta_rutina_perdida = True
                nombres_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                dia_perdido_nombre = nombres_dias[ultimo_dia_entrenamiento.weekday()]
    
    data = {
        'status': 'success',
        'tipo': 'cliente',
        'estado_color': estado_color,
        'estado': estado,
        'mensaje': mensaje,
        'cliente': {
            'id': cliente.id,
            'nombre': cliente.nombre,
            'cedula': cliente.cedula,
            'foto': cliente.foto_perfil.url if cliente.foto_perfil else None
        },
        'suscripcion': {
            'plan': suscripcion.plan.nombre,
            'fecha_inscripcion': suscripcion.fecha_inscripcion.strftime('%d/%m/%Y'),
            'fecha_vencimiento': vencimiento.strftime('%d/%m/%Y'),
            'metodo_pago_usual': metodo_pago_usual,
        },
        'rutina': {
            'dia_hoy': rutina_dia_str,
            'alerta_perdida': alerta_rutina_perdida,
            'dia_perdido_nombre': dia_perdido_nombre
        }
    }
    
    return JsonResponse(data)

def dashboard(request):
    hoy = timezone.now().date()
    
    clientes_totales = Cliente.objects.count()
    suscripciones_activas = Suscripcion.objects.filter(estado='Activo').count()
    suscripciones_vencidas = Suscripcion.objects.filter(estado='Vencido').count()
    asistencias_hoy = Asistencia.objects.filter(fecha_hora_entrada__date=hoy).count()
    
    # Estadísticas de planes activos
    planes_activos = Suscripcion.objects.filter(estado='Activo') \
        .values('plan__nombre') \
        .annotate(total=Count('id')) \
        .order_by('-total')
    
    context = {
        'clientes_totales': clientes_totales,
        'suscripciones_activas': suscripciones_activas,
        'suscripciones_vencidas': suscripciones_vencidas,
        'asistencias_hoy': asistencias_hoy,
        'planes_activos': planes_activos,
    }
    return render(request, 'gym/dashboard.html', context)

def cliente_crear(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear el Cliente
                    cliente = form.save(commit=False)
                    
                    # Manejo de la foto base64
                    foto_base64 = form.cleaned_data.get('foto_base64')
                    if foto_base64:
                        format, imgstr = foto_base64.split(';base64,') 
                        ext = format.split('/')[-1] 
                        data = ContentFile(base64.b64decode(imgstr), name=f'{cliente.cedula}.{ext}')
                        cliente.foto_perfil = data
                        
                        # Extraer descriptor facial con face_recognition
                        descriptor = get_face_encoding_from_base64(imgstr)
                        if descriptor:
                            cliente.descriptor_facial = descriptor
                        
                    cliente.save()
                    
                    # 2. Crear la Suscripcion
                    plan = form.cleaned_data.get('plan')
                    fecha_inscripcion = form.cleaned_data.get('fecha_inscripcion')
                    fecha_vencimiento = fecha_inscripcion + timedelta(days=plan.duracion_dias)
                    
                    suscripcion = Suscripcion.objects.create(
                        cliente=cliente,
                        plan=plan,
                        fecha_inscripcion=fecha_inscripcion,
                        fecha_vencimiento=fecha_vencimiento,
                        estado='Activo'
                    )
                    
                    # 3. Crear el Pago
                    metodo_pago = form.cleaned_data.get('metodo_pago')
                    Pago.objects.create(
                        suscripcion=suscripcion,
                        monto=plan.tarifa,
                        metodo_pago=metodo_pago,
                        fecha_pago=timezone.now().date()
                    )
                    
                return redirect('dashboard')
            except Exception as e:
                form.add_error(None, f"Ocurrió un error al procesar el registro: {e}")
    else:
        form = RegistroClienteForm()
        
    return render(request, 'gym/cliente_form.html', {'form': form})

def renovar_suscripcion(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    ultima_suscripcion = cliente.suscripciones.order_by('-fecha_vencimiento').first()
    
    if request.method == 'POST':
        form = RenovacionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    nuevo_plan = form.cleaned_data.get('plan')
                    metodo_pago = form.cleaned_data.get('metodo_pago')
                    hoy = timezone.now().date()
                    
                    # Si el plan es el mismo, agregamos un pago a la suscripción actual.
                    # El modelo Pago se encargará de extender la fecha de vencimiento.
                    if ultima_suscripcion and ultima_suscripcion.plan == nuevo_plan:
                        Pago.objects.create(
                            suscripcion=ultima_suscripcion,
                            monto=nuevo_plan.tarifa,
                            metodo_pago=metodo_pago,
                            fecha_pago=hoy
                        )
                    else:
                        # Si cambia de plan o no tenía suscripción, creamos una nueva
                        fecha_inicio = hoy
                        if ultima_suscripcion and ultima_suscripcion.fecha_vencimiento and ultima_suscripcion.fecha_vencimiento > hoy:
                            # Si renueva antes de tiempo pero cambia de plan, comienza al vencer la actual (o hoy si lo prefieres)
                            # Para un gimnasio, si cambia de plan suele iniciar al vencer el actual
                            fecha_inicio = ultima_suscripcion.fecha_vencimiento
                            
                        fecha_venc = fecha_inicio + timedelta(days=nuevo_plan.duracion_dias)
                        nueva_suscripcion = Suscripcion.objects.create(
                            cliente=cliente,
                            plan=nuevo_plan,
                            fecha_inscripcion=fecha_inicio,
                            fecha_vencimiento=fecha_venc,
                            estado='Activo'
                        )
                        Pago.objects.create(
                            suscripcion=nueva_suscripcion,
                            monto=nuevo_plan.tarifa,
                            metodo_pago=metodo_pago,
                            fecha_pago=hoy
                        )
                return redirect('dashboard')
            except Exception as e:
                form.add_error(None, f"Error al procesar la renovación: {e}")
    else:
        # Pre-seleccionar el último plan si existe
        initial_data = {}
        if ultima_suscripcion:
            initial_data['plan'] = ultima_suscripcion.plan
            
            ultimo_pago = ultima_suscripcion.pagos.order_by('-fecha_pago').first()
            if ultimo_pago:
                initial_data['metodo_pago'] = ultimo_pago.metodo_pago
                
        form = RenovacionForm(initial=initial_data)
    config = ConfiguracionSistema.get_config()
    import json
    from .models import Plan
    planes_data = {str(p.id): float(p.tarifa) for p in Plan.objects.all()}
    
    return render(request, 'gym/renovacion_form.html', {
        'form': form, 
        'cliente': cliente,
        'ultima_suscripcion': ultima_suscripcion,
        'hoy': timezone.now().date(),
        'tasa_bcv': config.tasa_bcv,
        'planes_data': json.dumps(planes_data)
    })

def cliente_list(request):
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    plan_nombre = request.GET.get('plan_nombre', '')
    
    clientes_queryset = Cliente.objects.prefetch_related('suscripciones__plan').all()
    
    if query:
        clientes_queryset = clientes_queryset.filter(
            Q(nombre__icontains=query) | 
            Q(cedula__icontains=query) |
            Q(telefono__icontains=query)
        )
        
    clientes_list = []
    
    hoy = timezone.now().date()
    for c in clientes_queryset:
        subs = list(c.suscripciones.all())
        subs.sort(key=lambda x: x.fecha_vencimiento if x.fecha_vencimiento else timezone.datetime.min.date(), reverse=True)
        latest_sub = subs[0] if subs else None
        
        # Actualización dinámica en memoria del estado según la fecha de vencimiento real
        if latest_sub and latest_sub.fecha_vencimiento:
            if latest_sub.fecha_vencimiento < hoy:
                latest_sub.estado = 'Vencido'
            else:
                latest_sub.estado = 'Activo'
                
        c.latest_sub = latest_sub
        
        if estado:
            if not latest_sub or latest_sub.estado != estado.capitalize():
                continue
        if plan_nombre:
            if not latest_sub or latest_sub.plan.nombre != plan_nombre:
                continue
                
        clientes_list.append(c)
        
    if estado == 'Vencido':
        clientes_list.sort(key=lambda x: x.latest_sub.fecha_vencimiento if x.latest_sub and x.latest_sub.fecha_vencimiento else timezone.datetime.min.date(), reverse=True)
    elif estado == 'Activo':
        clientes_list.sort(key=lambda x: x.nombre)
    elif plan_nombre:
        clientes_list.sort(key=lambda x: x.latest_sub.fecha_inscripcion if x.latest_sub else timezone.datetime.min.date(), reverse=True)
    else:
        if not query:
            clientes_list.sort(key=lambda x: x.id, reverse=True)
            
    return render(request, 'gym/cliente_list.html', {'clientes': clientes_list, 'query': query})

def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteEditForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente_obj = form.save(commit=False)
            foto_base64 = form.cleaned_data.get('foto_base64')
            if foto_base64:
                format, imgstr = foto_base64.split(';base64,') 
                ext = format.split('/')[-1] 
                data = ContentFile(base64.b64decode(imgstr), name=f'{cliente_obj.cedula}.{ext}')
                cliente_obj.foto_perfil = data
            cliente_obj.save()
            return redirect('cliente_list')
    else:
        form = ClienteEditForm(instance=cliente)
    return render(request, 'gym/cliente_editar.html', {'form': form, 'cliente': cliente})

def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('cliente_list')
    return render(request, 'gym/cliente_confirm_delete.html', {'cliente': cliente})

def asistencia_list(request):
    hoy = timezone.now().date()
    asistencias = Asistencia.objects.filter(fecha_hora_entrada__date=hoy).order_by('-fecha_hora_entrada')
    return render(request, 'gym/asistencia_list.html', {'asistencias': asistencias})

# ==========================================
# GESTIÓN DE PLANES (CRUD)
# ==========================================
def plan_list(request):
    planes = Plan.objects.all().order_by('tarifa')
    return render(request, 'gym/plan_list.html', {'planes': planes})

def plan_crear(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('plan_list')
    else:
        form = PlanForm()
    return render(request, 'gym/plan_form.html', {'form': form, 'titulo': 'Crear Nuevo Plan'})

def plan_editar(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect('plan_list')
    else:
        form = PlanForm(instance=plan)
    return render(request, 'gym/plan_form.html', {'form': form, 'titulo': 'Editar Plan'})

def plan_eliminar(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        plan.delete()
        return redirect('plan_list')
    return render(request, 'gym/plan_confirm_delete.html', {'plan': plan})

# ==========================================
# GESTIÓN DE PERSONAL (CRUD)
# ==========================================
def personal_list(request):
    personal = Personal.objects.all().order_by('cargo_especialidad', 'nombre_completo')
    return render(request, 'gym/personal_list.html', {'personal': personal})

def personal_crear(request):
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    miembro = form.save(commit=False)
                    foto_base64 = form.cleaned_data.get('foto_base64')
                    if foto_base64:
                        format, imgstr = foto_base64.split(';base64,') 
                        ext = format.split('/')[-1] 
                        data = ContentFile(base64.b64decode(imgstr), name=f'{miembro.nombre_completo.replace(" ", "_")}.{ext}')
                        miembro.foto_perfil = data
                        
                        descriptor = get_face_encoding_from_base64(imgstr)
                        if descriptor:
                            miembro.descriptor_facial = descriptor
                            
                    miembro.save()
                    return redirect('personal_list')
            except Exception as e:
                form.add_error(None, f"Error al registrar: {str(e)}")
    else:
        form = PersonalForm()
    return render(request, 'gym/personal_form.html', {'form': form, 'titulo': 'Registrar Personal'})

def personal_editar(request, pk):
    miembro = get_object_or_404(Personal, pk=pk)
    if request.method == 'POST':
        form = PersonalForm(request.POST, instance=miembro)
        if form.is_valid():
            try:
                with transaction.atomic():
                    miembro = form.save(commit=False)
                    foto_base64 = form.cleaned_data.get('foto_base64')
                    if foto_base64:
                        format, imgstr = foto_base64.split(';base64,') 
                        ext = format.split('/')[-1] 
                        data = ContentFile(base64.b64decode(imgstr), name=f'{miembro.nombre_completo.replace(" ", "_")}.{ext}')
                        miembro.foto_perfil = data
                        
                        descriptor = get_face_encoding_from_base64(imgstr)
                        if descriptor:
                            miembro.descriptor_facial = descriptor
                            
                    miembro.save()
                    return redirect('personal_list')
            except Exception as e:
                form.add_error(None, f"Error al editar: {str(e)}")
    else:
        form = PersonalForm(instance=miembro)
    return render(request, 'gym/personal_form.html', {'form': form, 'titulo': 'Editar Personal'})

def personal_eliminar(request, pk):
    miembro = get_object_or_404(Personal, pk=pk)
    if request.method == 'POST':
        miembro.delete()
        return redirect('personal_list')
    return render(request, 'gym/personal_confirm_delete.html', {'miembro': miembro})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def validar_rostro(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            foto_base64 = data.get('image')
            if not foto_base64:
                return JsonResponse({'status': 'not_found', 'error': 'No image provided'})
                
            format, imgstr = foto_base64.split(';base64,')
            encodings_detectados = get_face_encoding_from_base64(imgstr)
            
            if not encodings_detectados:
                return JsonResponse({'status': 'not_found'})
                
            # Buscar coincidencia en la DB
            clientes = Cliente.objects.exclude(descriptor_facial__isnull=True).exclude(descriptor_facial='')
            personal_staff = Personal.objects.exclude(descriptor_facial__isnull=True).exclude(descriptor_facial='')
            
            mejor_match = None
            menor_distancia = 0.5  # Tolerancia
            tipo_match = None
            
            for cliente in clientes:
                if cliente.descriptor_facial:
                    db_encoding = np.array(cliente.descriptor_facial)
                    distancia = face_recognition.face_distance([db_encoding], np.array(encodings_detectados))[0]
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        mejor_match = cliente
                        tipo_match = 'cliente'
                        
            for staff in personal_staff:
                if staff.descriptor_facial:
                    db_encoding = np.array(staff.descriptor_facial)
                    distancia = face_recognition.face_distance([db_encoding], np.array(encodings_detectados))[0]
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        mejor_match = staff
                        tipo_match = 'staff'
                        
            if mejor_match and tipo_match == 'staff':
                Asistencia.objects.create(personal=mejor_match)
                return JsonResponse({
                    'status': 'success',
                    'tipo': 'staff',
                    'estado_color': 'Verde',
                    'estado': 'Activo',
                    'mensaje': f'Bienvenida al equipo, {mejor_match.nombre_completo}',
                    'cliente': {
                        'id': mejor_match.id,
                        'nombre': mejor_match.nombre_completo,
                        'cedula': mejor_match.cedula if mejor_match.cedula else 'N/A',
                        'foto': mejor_match.foto_perfil.url if mejor_match.foto_perfil else None
                    },
                    'suscripcion': {
                        'plan': mejor_match.cargo_especialidad,
                        'fecha_inscripcion': 'N/A',
                        'fecha_vencimiento': 'N/A',
                        'metodo_pago_usual': 'N/A',
                    }
                })
                        
            elif mejor_match and tipo_match == 'cliente':
                mejor_cliente = mejor_match
                # Obtener la última suscripción
                suscripcion = mejor_cliente.suscripciones.order_by('-fecha_vencimiento').first()
                
                if not suscripcion or not suscripcion.fecha_vencimiento:
                    return JsonResponse({
                        'status': 'success',
                        'tipo': 'cliente',
                        'error': 'El cliente no tiene suscripciones activas', 
                        'estado_color': 'Rojo',
                        'estado': 'Inactivo',
                        'cliente': {
                            'id': mejor_cliente.id,
                            'nombre': mejor_cliente.nombre,
                            'cedula': mejor_cliente.cedula,
                            'foto': mejor_cliente.foto_perfil.url if mejor_cliente.foto_perfil else None
                        }
                    })
                    
                hoy = timezone.now().date()
                vencimiento = suscripcion.fecha_vencimiento
                
                # Obtener configuración de días de gracia
                config = ConfiguracionSistema.get_config()
                dias_gracia = config.dias_gracia
                
                limite_gracia = vencimiento + timedelta(days=dias_gracia)
                
                # Lógica del Semáforo
                if hoy <= vencimiento:
                    # Si faltan 3 días o menos, lanzar pre-alerta de renovación
                    if (vencimiento - hoy).days <= 3:
                        estado_color = 'Amarillo'
                        estado = 'Por vencer'
                        mensaje = f'Acceso Permitido. Recuerde que su plan vence en {(vencimiento - hoy).days} días.'
                    else:
                        estado_color = 'Verde'
                        estado = 'Activo'
                        mensaje = 'Acceso Permitido'
                    registrar_asistencia = True
                elif hoy <= limite_gracia:
                    estado_color = 'Amarillo'
                    estado = 'Por vencer'
                    mensaje = f'Alerta: Mensualidad vencida. En periodo de gracia ({dias_gracia} días).'
                    registrar_asistencia = True
                else:
                    estado_color = 'Rojo'
                    estado = 'Inactivo'
                    mensaje = 'Acceso Denegado: Superó los días de gracia, exige pago.'
                    registrar_asistencia = False
                    
                if registrar_asistencia:
                    Asistencia.objects.create(cliente=mejor_cliente)
                    
                ultimo_pago = suscripcion.pagos.order_by('-fecha_pago').first()
                metodo_pago_usual = ultimo_pago.metodo_pago if ultimo_pago else 'No registrado'
                
                data = {
                    'status': 'success',
                    'tipo': 'cliente',
                    'estado_color': estado_color,
                    'estado': estado,
                    'mensaje': mensaje,
                    'cliente': {
                        'id': mejor_cliente.id,
                        'nombre': mejor_cliente.nombre,
                        'cedula': mejor_cliente.cedula,
                        'foto': mejor_cliente.foto_perfil.url if mejor_cliente.foto_perfil else None
                    },
                    'suscripcion': {
                        'plan': suscripcion.plan.nombre,
                        'fecha_inscripcion': suscripcion.fecha_inscripcion.strftime('%d/%m/%Y'),
                        'fecha_vencimiento': vencimiento.strftime('%d/%m/%Y'),
                        'metodo_pago_usual': metodo_pago_usual,
                    }
                }
                
                return JsonResponse(data)
            else:
                return JsonResponse({'status': 'unknown_face'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'invalid_method'})

def rutina_crear(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        import json
        from django.db import transaction
        try:
            data = json.loads(request.body)
            with transaction.atomic():
                if data.get('action') == 'delete':
                    asignacion = AsignacionCliente.objects.filter(cliente=cliente).first()
                    if asignacion:
                        mesociclo = asignacion.mesociclo
                        asignacion.delete()
                        if mesociclo:
                            mesociclo.delete()
                    return JsonResponse({'status': 'success', 'message': 'Rutina eliminada correctamente'})

                coach = None
                if data.get('coach_id'):
                    coach = Personal.objects.filter(id=data['coach_id']).first()
                    
                mesociclo_id = data.get('mesociclo_id')
                if mesociclo_id:
                    mesociclo = Mesociclo.objects.get(id=mesociclo_id)
                    mesociclo.nombre = data.get('nombre', 'Rutina Personalizada')
                    mesociclo.duracion_semanas = int(data.get('duracion', 4))
                    mesociclo.coach = coach
                    mesociclo.save()
                    # Borrar los días anteriores para recrearlos
                    DiaRutina.objects.filter(mesociclo=mesociclo).delete()
                    
                    asignacion_existente = AsignacionCliente.objects.filter(mesociclo=mesociclo).first()
                    if asignacion_existente:
                        asignacion_existente.dias_activos = data.get('dias_activos', [])
                        asignacion_existente.save()
                else:
                    mesociclo = Mesociclo.objects.create(
                        nombre=data.get('nombre', 'Rutina Personalizada'),
                        duracion_semanas=int(data.get('duracion', 4)),
                        coach=coach
                    )
                
                for dia_data in data.get('dias', []):
                    dia = DiaRutina.objects.create(
                        mesociclo=mesociclo,
                        semana=int(dia_data.get('semana', 1)),
                        numero_dia=int(dia_data.get('numero', 1)),
                        enfoque=dia_data.get('enfoque', '')
                    )
                    
                    for ej_data in dia_data.get('ejercicios', []):
                        EjercicioRutina.objects.create(
                            dia_rutina=dia,
                            nombre_ejercicio=ej_data.get('nombre', ''),
                            series=ej_data.get('series', ''),
                            repeticiones=ej_data.get('detalles', ''),
                            peso_asignado=ej_data.get('peso', '')
                        )
                
                if not mesociclo_id:
                    AsignacionCliente.objects.create(
                        cliente=cliente,
                        mesociclo=mesociclo,
                        fecha_inicio=timezone.localdate(),
                        dias_activos=data.get('dias_activos', [])
                    )
                
            return JsonResponse({'status': 'success', 'message': 'Rutina creada y asignada correctamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    import json
    asignacion = AsignacionCliente.objects.filter(cliente=cliente).order_by('-fecha_inicio').first()
    rutina_activa_json = None
    
    if asignacion and not request.GET.get('nueva'):
        m = asignacion.mesociclo
        rutina_activa_data = {
            'id': m.id,
            'nombre': m.nombre,
            'duracion': m.duracion_semanas,
            'coach_id': m.coach.id if m.coach else '',
            'dias_activos': asignacion.dias_activos if asignacion else [],
            'dias': []
        }
        
        for d in m.dias.all():
            dia_data = {
                'id': f"d_{d.id}",
                'semana': d.semana,
                'numero': d.numero_dia,
                'enfoque': d.enfoque,
                'ejercicios': []
            }
            for e in d.ejercicios.all():
                dia_data['ejercicios'].append({
                    'id': f"e_{e.id}",
                    'nombre': e.nombre_ejercicio,
                    'series': e.series,
                    'detalles': e.repeticiones,
                    'peso': e.peso_asignado or ''
                })
            rutina_activa_data['dias'].append(dia_data)
        
        rutina_activa_json = json.dumps(rutina_activa_data)

    coaches = Personal.objects.exclude(cargo_especialidad__in=['Recepcionista', 'Gerencia'])
    return render(request, 'gym/rutina_crear.html', {
        'cliente': cliente, 
        'coaches': coaches,
        'rutina_activa_json': rutina_activa_json
    })

# --- FASE 3: RUTINAS Y PROGRESIÓN ---

def perfil_entrenamiento_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    asignacion = AsignacionCliente.objects.filter(cliente=cliente).order_by('-fecha_inicio').first()
    
    if not asignacion:
        return render(request, 'gym/rutina_cliente.html', {
            'cliente': cliente,
            'mensaje': 'Este cliente no tiene una rutina asignada.'
        })
        
    mesociclo = asignacion.mesociclo
    fecha_inicio = asignacion.fecha_inicio
    hoy = timezone.localdate()
    
    # Calcular progreso total y secuencia cronológica
    dias_activos = asignacion.dias_activos or [0, 1, 2, 3, 4, 5, 6]
    dias_activos = sorted([int(d) for d in dias_activos])
    dias_por_semana = len(dias_activos)
    if dias_por_semana == 0:
        dias_por_semana = 7
        
    total_dias_plan = mesociclo.duracion_semanas * dias_por_semana
    fechas_entrenamiento = []
    fecha_iter = fecha_inicio
    
    # Generar la secuencia cronológica exacta de todos los días de entrenamiento
    while len(fechas_entrenamiento) < total_dias_plan:
        if fecha_iter.weekday() in dias_activos:
            fechas_entrenamiento.append(fecha_iter)
        fecha_iter += timedelta(days=1)

    dias_asistidos_totales = Asistencia.objects.filter(cliente=cliente, fecha_hora_entrada__date__gte=fecha_inicio).values('fecha_hora_entrada__date').distinct().count()
    progreso_porcentaje = int((dias_asistidos_totales / total_dias_plan) * 100) if total_dias_plan > 0 else 0
    progreso_porcentaje = min(100, progreso_porcentaje)
    
    # Calcular en qué semana/día de rutina estamos HOY
    semana_cronologica = 1
    dia_cronologico = 1
    
    if hoy in fechas_entrenamiento:
        idx_hoy = fechas_entrenamiento.index(hoy)
        semana_cronologica = (idx_hoy // dias_por_semana) + 1
        dia_cronologico = (idx_hoy % dias_por_semana) + 1
    elif hoy > fechas_entrenamiento[-1]:
        semana_cronologica = mesociclo.duracion_semanas
        dia_cronologico = dias_por_semana
    elif hoy < fecha_inicio:
        semana_cronologica = 1
        dia_cronologico = 1
    else:
        # Hoy es un día de descanso en medio del plan, buscar el último día entrenado
        pasados = [f for f in fechas_entrenamiento if f < hoy]
        if pasados:
            idx_pasado = len(pasados) - 1
            semana_cronologica = (idx_pasado // dias_por_semana) + 1
            dia_cronologico = (idx_pasado % dias_por_semana) + 1

    # Parámetros URL
    semana_seleccionada = request.GET.get('semana')
    if semana_seleccionada and semana_seleccionada.isdigit():
        semana_seleccionada = int(semana_seleccionada)
    else:
        semana_seleccionada = semana_cronologica
        
    dia_seleccionado = request.GET.get('dia')
    if dia_seleccionado and dia_seleccionado.isdigit():
        dia_seleccionado = int(dia_seleccionado)
    else:
        dia_seleccionado = dia_cronologico
        if semana_seleccionada != semana_cronologica:
            dia_seleccionado = 1
            
    rango_semanas = list(range(1, mesociclo.duracion_semanas + 1))
    
    # Fechas correspondientes a la semana seleccionada
    start_idx = (semana_seleccionada - 1) * dias_por_semana
    end_idx = min(start_idx + dias_por_semana, len(fechas_entrenamiento))
    fechas_semana_seleccionada = fechas_entrenamiento[start_idx:end_idx]

    # Asistencias de esa semana para la cuadrícula
    dias_asistidos_semana = set()
    if fechas_semana_seleccionada:
        asistencias_semana = Asistencia.objects.filter(
            cliente=cliente,
            fecha_hora_entrada__date__in=fechas_semana_seleccionada
        ).values_list('fecha_hora_entrada__date', flat=True)
        dias_asistidos_semana = set(asistencias_semana)

    # Construir cuadrícula cronológica dinámica (solo días activos)
    cuadricula = []
    dias_rutina_obj = {d.numero_dia: d for d in DiaRutina.objects.filter(mesociclo=mesociclo, semana=semana_seleccionada)}
    
    for idx, fecha_dia in enumerate(fechas_semana_seleccionada):
        numero_dia_rutina = idx + 1
        asistio = fecha_dia in dias_asistidos_semana
        dia_r = dias_rutina_obj.get(numero_dia_rutina)
        enfoque = dia_r.enfoque if dia_r else 'Descanso'
        
        cuadricula.append({
            'numero_dia': numero_dia_rutina,
            'fecha': fecha_dia,
            'es_hoy': fecha_dia == hoy,
            'asistio': asistio,
            'enfoque': enfoque,
            'seleccionado': numero_dia_rutina == dia_seleccionado
        })
        
    # Ejercicios del día seleccionado
    dia_rutina_actual = dias_rutina_obj.get(dia_seleccionado)
    
    fecha_seleccionada = hoy
    if start_idx + (dia_seleccionado - 1) < len(fechas_entrenamiento):
        fecha_seleccionada = fechas_entrenamiento[start_idx + (dia_seleccionado - 1)]
    
    ejercicios_con_progresion = []
    if dia_rutina_actual:
        ejercicios = dia_rutina_actual.ejercicios.all()
        for ej in ejercicios:
            prog = RegistroProgresion.objects.filter(cliente=cliente, ejercicio=ej, fecha=fecha_seleccionada).first()
            ejercicios_con_progresion.append({
                'ejercicio': ej,
                'peso_registrado': prog.peso_levantado if prog else ''
            })

    return render(request, 'gym/rutina_cliente.html', {
        'cliente': cliente,
        'mesociclo': mesociclo,
        'semana_seleccionada': semana_seleccionada,
        'semana_cronologica': semana_cronologica,
        'rango_semanas': rango_semanas,
        'progreso_porcentaje': progreso_porcentaje,
        'cuadricula': cuadricula,
        'dia_rutina_actual': dia_rutina_actual,
        'ejercicios_con_progresion': ejercicios_con_progresion,
        'fecha_seleccionada': fecha_seleccionada
    })

def guardar_peso_ajax(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            ejercicio_id = data.get('ejercicio_id')
            peso = data.get('peso')
            fecha_str = data.get('fecha')
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            ejercicio = get_object_or_404(EjercicioRutina, id=ejercicio_id)
            
            # Parse the date passed from the frontend, default to today
            if fecha_str:
                from datetime import datetime
                fecha_guardado = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha_guardado = timezone.localdate()
            
            registro, created = RegistroProgresion.objects.get_or_create(
                cliente=cliente,
                ejercicio=ejercicio,
                fecha=fecha_guardado,
                defaults={'peso_levantado': peso}
            )
            
            if not created:
                registro.peso_levantado = peso
                registro.save()
                
            return JsonResponse({'status': 'success', 'message': 'Peso guardado'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'invalid_method'})
