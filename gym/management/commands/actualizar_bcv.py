from django.core.management.base import BaseCommand
from gym.utils.bcv_scraper import actualizar_tasa_bcv

class Command(BaseCommand):
    help = 'Actualiza la tasa del dólar BCV en la configuración del sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando extracción de la tasa BCV...')
        tasa = actualizar_tasa_bcv()
        if tasa:
            self.stdout.write(self.style.SUCCESS(f'Exito! Tasa actualizada a: Bs. {tasa}'))
        else:
            self.stdout.write(self.style.ERROR('Fallo al actualizar la tasa BCV.'))
