import logging
from datetime import datetime, time, timedelta
from io import BytesIO

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from PIL import Image, ImageOps

from .models import Planet

logger = logging.getLogger(__name__)

CACHE_KEY = "daily_planet_from_microservice_id"
NEGATIVE_CACHE_KEY = "daily_planet_from_microservice:unavailable"
NEGATIVE_CACHE_TIMEOUT = 30
THUMBNAIL_SIZE = (128, 128)


def _mark_microservice_unavailable():
    cache.set(NEGATIVE_CACHE_KEY, True, timeout=NEGATIVE_CACHE_TIMEOUT)


def get_daily_planet_from_microservice():
    if cache.get(NEGATIVE_CACHE_KEY):
        return None

    planet_id = cache.get(CACHE_KEY)

    if planet_id is not None:
        planet = Planet.objects.filter(pk=planet_id).first()
        if planet is not None:
            return planet
        cache.delete(CACHE_KEY)

    try:
        url = f"{settings.FASTAPI_URL}/planet/today"
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        planet_id = response.json().get("planet_id")

        if planet_id is None:
            _mark_microservice_unavailable()
            return None

        planet = Planet.objects.filter(pk=planet_id).first()
        if planet is not None:
            cache.delete(NEGATIVE_CACHE_KEY)
            cache.set(CACHE_KEY, planet_id, timeout=60 * 10)
        else:
            _mark_microservice_unavailable()
        return planet

    except requests.exceptions.Timeout:
        logger.warning("FastAPI timeout while fetching planet of the day")
        _mark_microservice_unavailable()
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("FastAPI connection error while fetching planet of the day")
        _mark_microservice_unavailable()
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("FastAPI request failed: %s", e)
        _mark_microservice_unavailable()
        return None
    except ValueError as e:
        logger.warning("Invalid JSON from FastAPI: %s", e)
        _mark_microservice_unavailable()
        return None


def seconds_until_midnight():
    now = timezone.localtime()
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=now.tzinfo)
    return max(60, int((tomorrow - now).total_seconds()))


def get_daily_planet_thumbnail(planet):
    if planet is None or not planet.image:
        return None

    cache_key = f"daily_planet_thumbnail:{planet.pk}:{timezone.localdate().isoformat()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        with planet.image.open("rb") as source:
            image = Image.open(source)
            image.load()
    except (OSError, ValueError) as e:
        logger.warning("Cannot open image for planet %s: %s", planet.pk, e)
        return None

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (0, 0, 0))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    thumbnail = ImageOps.fit(image, THUMBNAIL_SIZE, Image.LANCZOS)
    buffer = BytesIO()
    thumbnail.save(buffer, "WEBP", quality=85, method=6)
    data = buffer.getvalue()

    cache.set(cache_key, data, timeout=seconds_until_midnight())
    return data


def separate_first_line(obj):
    if not obj.text:
        return "", ""
    lines = obj.text.splitlines()
    first_line = lines[0] if lines else ""
    remaining_text = "\n".join(lines[1:])
    return first_line, remaining_text
