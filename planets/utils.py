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
    print("=== DEBUG: start get_daily_planet_from_microservice")

    # 1. Проверяем кеш
    planet_id = cache.get('daily_planet_from_microservice_id')
    print(f"=== DEBUG: cached planet_id = {planet_id}")

    if planet_id is not None:
        try:
            planet = Planet.objects.get(pk=planet_id)
            print(f"=== DEBUG: found planet from cache: {planet}")
            return planet
        except Planet.DoesNotExist:
            print("=== DEBUG: planet from cache not found in DB, clearing cache")
            cache.delete('daily_planet_from_microservice_id')

    # 2. Запрос к FastAPI
    try:
        url = f"{settings.FASTAPI_URL}/planet/today"
        print(f"=== DEBUG: requesting {url}")
        response = requests.get(url, timeout=2)  # таймаут добавлен
        print(f"=== DEBUG: response status = {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"=== DEBUG: response data = {data}")

        planet_id = data.get('planet_id')
        print(f"=== DEBUG: planet_id from response = {planet_id}")

        if planet_id is None:
            print("=== DEBUG: no planet_id in response")
            return None

        planet = Planet.objects.filter(pk=planet_id).first()
        print(f"=== DEBUG: planet from DB = {planet}")

        if planet:
            cache.set('daily_planet_from_microservice_id', planet_id, timeout=60 * 10)
            print("=== DEBUG: cached planet_id")
        return planet

    except requests.exceptions.Timeout:
        print("=== DEBUG: EXCEPTION: Timeout")
        logger.error("FastAPI timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("=== DEBUG: EXCEPTION: ConnectionError")
        logger.error("FastAPI connection error")
        return None
    except requests.exceptions.RequestException as e:
        print(f"=== DEBUG: EXCEPTION: {e}")
        logger.error("FastAPI request failed: %s", e)
        return None
    except ValueError as e:
        print(f"=== DEBUG: EXCEPTION: Invalid JSON: {e}")
        logger.error("Invalid JSON from FastAPI: %s", e)
        return None


def separate_first_line(obj):
    first_line = obj.text.splitlines()[0] if obj.text else ''
    lines = obj.text.splitlines()
    remaining_text = "\n".join(lines[1:])
    return first_line, remaining_text