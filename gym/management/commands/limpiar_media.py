from django.core.management.base import BaseCommand
from gym.models import Cliente, Personal
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Limpia imágenes huérfanas en la carpeta media que no están referenciadas en la base de datos'

    def handle(self, *args, **kwargs):
        valid_files = set()
        
        # Obtener todas las fotos referenciadas por Clientes
        for c in Cliente.objects.all():
            if c.foto_perfil:
                valid_files.add(os.path.basename(c.foto_perfil.name))
                
        # Obtener todas las fotos referenciadas por Personal
        for p in Personal.objects.all():
            if getattr(p, 'foto_perfil', None):
                valid_files.add(os.path.basename(p.foto_perfil.name))

        clientes_dir = os.path.join(settings.MEDIA_ROOT, 'clientes')
        personal_dir = os.path.join(settings.MEDIA_ROOT, 'personal')

        deleted_count = 0
        v_test_count = 0

        # Limpiar carpeta clientes
        if os.path.exists(clientes_dir):
            for f in os.listdir(clientes_dir):
                if f == '.gitkeep':
                    continue
                
                # Si el archivo no está en los archivos válidos referenciados
                if f not in valid_files:
                    try:
                        os.remove(os.path.join(clientes_dir, f))
                        deleted_count += 1
                        if f.startswith('V') and f.endswith('.jpeg'):
                            v_test_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error eliminando {f}: {e}'))

        # Limpiar carpeta personal
        if os.path.exists(personal_dir):
            for f in os.listdir(personal_dir):
                if f == '.gitkeep':
                    continue
                
                if f not in valid_files:
                    try:
                        os.remove(os.path.join(personal_dir, f))
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error eliminando {f}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Limpieza completada con éxito.'))
        self.stdout.write(self.style.WARNING(f'Total de archivos huérfanos eliminados: {deleted_count}'))
        self.stdout.write(self.style.WARNING(f'De los cuales {v_test_count} eran archivos de prueba V*.jpeg'))
