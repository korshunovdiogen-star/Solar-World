import os

from django.core.exceptions import ImproperlyConfigured

_TRUE_VALUES = {"1", "true", "yes", "on"}
_PRODUCTION_MARKERS = ("RENDER", "RAILWAY_ENVIRONMENT", "DYNO")


def env_str(name, default=None):
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def env_bool(name, default=False):
    """1/true/yes/on считаются True."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in _TRUE_VALUES


def env_int(name, default=0):
    value = env_str(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} должен быть целым числом, получено: {value!r}") from exc


def env_list(name, default=()):
    """Список через запятую; пустые элементы отбрасываются."""
    value = os.getenv(name)
    if not value or not value.strip():
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def detect_environment():
    """ENVIRONMENT важнее автоматических признаков хостингов."""
    explicit = env_str("ENVIRONMENT")
    if explicit:
        return explicit.lower()
    if any(os.getenv(marker) for marker in _PRODUCTION_MARKERS):
        return "prod"
    return "local"
