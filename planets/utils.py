import requests
from django.conf import settings
from django.core.cache import cache
from .models import Planet
import logging

logger = logging.getLogger(__name__)

def get_daily_planet_from_microservice():
    """
    Получает ID планеты дня от микросервиса,
    возвращает объект Planet.
    Если микросервис недоступен или планета не найдена — возвращает None.
    """


    try:
        response = requests.get(
            f"{settings.FASTAPI_URL}/planet/today",
        )
        response.raise_for_status()
        data = response.json()
        planet_id = data.get('planet_id')
        if planet_id is None:
            logger.error("FastAPI response missing 'planet_id' key: %s", data)
            return None

        planet = Planet.objects.filter(pk=planet_id).first()
        if planet is None:
            logger.warning("Planet with id %s not found in DB", planet_id)
            return None

        return planet

    except requests.exceptions.Timeout:
        logger.error("FastAPI timeout")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("FastAPI connection error")
        return None
    except requests.exceptions.RequestException as e:
        logger.error("FastAPI request failed: %s", e)
        return None
    except ValueError as e:
        logger.error("Invalid JSON from FastAPI: %s", e)
        return None




def separate_first_line(obj):
    first_line = obj.text.splitlines()[0] if obj.text else ''
    lines = obj.text.splitlines()
    remaining_text = "\n".join(lines[1:]) 
    return first_line, remaining_text