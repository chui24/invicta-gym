import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from gym.models import ConfiguracionSistema
import logging

logger = logging.logging.getLogger(__name__) if hasattr(logging, 'logging') else logging.getLogger(__name__)

def actualizar_tasa_bcv():
    """
    Consulta la página del BCV para obtener la tasa del dólar oficial,
    y actualiza la instancia Singleton de ConfiguracionSistema.
    """
    url = "https://www.bcv.org.ve/"
    try:
        # Se necesita verificar false a veces debido a problemas de SSL en la página del BCV
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # El BCV tiene un div con id 'dolar'
        dolar_div = soup.find('div', id='dolar')
        if dolar_div:
            # Dentro del div, hay un tag fuerte que contiene el valor
            valor_texto = dolar_div.find('strong').text.strip()
            # Reemplazar la coma por punto para poder castear a float/decimal
            valor_limpio = valor_texto.replace(',', '.')
            
            tasa_nueva = float(valor_limpio)
            
            # Actualizar DB
            config, _ = ConfiguracionSistema.objects.get_or_create(id=1, defaults={'dias_gracia': 0})
            config.tasa_bcv = tasa_nueva
            config.ultima_actualizacion_bcv = timezone.now()
            config.save()
            
            logger.info(f"Tasa BCV actualizada exitosamente a: {tasa_nueva}")
            return tasa_nueva
        else:
            logger.error("No se encontró el elemento del dólar en el HTML del BCV")
    except Exception as e:
        logger.error(f"Error actualizando tasa BCV: {e}")
        
    return None
