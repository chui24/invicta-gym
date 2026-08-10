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

from .models import Cliente, Asistencia, ConfiguracionSistema, Suscripcion, Pago, Plan, Personal
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
            'error': 'El cliente no tiene suscripciones activas', 
            'estado': 'Rojo',
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
        estado = 'Verde'
        mensaje = 'Acceso Permitido'
        registrar_asistencia = True
    elif hoy <= limite_gracia:
        estado = 'Amarillo'
        mensaje = f'Alerta: Mensualidad vencida. En periodo de gracia ({dias_gracia} días).'
        registrar_asistencia = True
    else:
        estado = 'Rojo'
        mensaje = 'Acceso Denegado: Superó los días de gracia, exige pago.'
        registrar_asistencia = False
        
    if registrar_asistencia:
        Asistencia.objects.create(cliente=cliente)
        
    ultimo_pago = suscripcion.pagos.order_by('-fecha_pago').first()
    metodo_pago_usual = ultimo_pago.metodo_pago if ultimo_pago else 'No registrado'
    
    data = {
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
        
    return render(request, 'gym/renovacion_form.html', {
        'form': form, 
        'cliente': cliente,
        'ultima_suscripcion': ultima_suscripcion
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
    
    for c in clientes_queryset:
        subs = list(c.suscripciones.all())
        subs.sort(key=lambda x: x.fecha_vencimiento if x.fecha_vencimiento else timezone.datetime.min.date(), reverse=True)
        latest_sub = subs[0] if subs else None
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
                    estado_color = 'Verde'
                    estado = 'Activo'
                    mensaje = 'Acceso Permitido'
                    registrar_asistencia = True
                elif hoy <= limite_gracia:
                    estado_color = 'Amarillo'
                    estado = 'Alerta'
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
