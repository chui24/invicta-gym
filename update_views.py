import re

with open('gym/views.py', 'r') as f:
    content = f.read()

# Make sure imports are there
if 'from django.contrib.auth.decorators import login_required' not in content:
    content = 'from django.contrib.auth.decorators import login_required\nfrom django.contrib.auth.forms import UserCreationForm\n' + content

# Add the new registro_admin view at the end
registro_code = """

@login_required
def registro_admin(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True  # Otorgar permisos de administrador
            user.save()
            messages.success(request, 'Usuario administrador creado exitosamente.')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/registro.html', {'form': form})
"""
if 'def registro_admin' not in content:
    content += registro_code

# Decorate all views
# Views are top-level defs that take request as first arg
views_to_decorate = [
    'validar_acceso_semaforo',
    'dashboard',
    'cliente_crear',
    'renovar_suscripcion',
    'cliente_list',
    'cliente_editar',
    'cliente_eliminar',
    'asistencia_list',
    'plan_list',
    'plan_crear',
    'plan_editar',
    'plan_eliminar',
    'personal_list',
    'personal_crear',
    'personal_editar',
    'personal_eliminar',
    'validar_rostro',
    'rutina_crear',
    'perfil_entrenamiento_cliente',
    'guardar_peso_ajax'
]

for view in views_to_decorate:
    pattern = rf"(?<!@login_required\n)def {view}\(request"
    content = re.sub(pattern, rf"@login_required\ndef {view}(request", content)

with open('gym/views.py', 'w') as f:
    f.write(content)

