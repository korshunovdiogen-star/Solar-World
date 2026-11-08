import logging

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save

from .models import Company, Mission, Planet, Satellite, SpaceAgency

logger = logging.getLogger(__name__)

MODELS_TO_WATCH = (Planet, Satellite, Mission, SpaceAgency, Company)


def _delete_pattern(pattern):
    """Удаляет ключи по маске; для бэкендов без delete_pattern чистит кеш."""
    delete_pattern = getattr(cache, "delete_pattern", None)
    if delete_pattern is None:
        cache.clear()
    else:
        delete_pattern(pattern)


def invalidate_detail_caches():
    """Сбрасывает кеш детальных страниц всех объектов."""
    _delete_pattern("*:detail")


def invalidate_catalog_cache():
    """Сбрасывает ответы @cache_page, включая /api/catalog/."""
    _delete_pattern("*cache_page*")


def invalidate_caches():
    logger.debug("Сброс кеша детальных страниц и каталога")
    invalidate_detail_caches()
    invalidate_catalog_cache()


def on_model_save(sender, instance, **kwargs):
    invalidate_caches()


def on_model_delete(sender, instance, **kwargs):
    invalidate_caches()


def on_m2m_change(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        invalidate_caches()


for model in MODELS_TO_WATCH:
    post_save.connect(
        on_model_save,
        sender=model,
        dispatch_uid=f"cache-post-save-{model.__name__}",
    )
    post_delete.connect(
        on_model_delete,
        sender=model,
        dispatch_uid=f"cache-post-delete-{model.__name__}",
    )

for through_model in (
    Mission.space_agency.through,
    Mission.target_planets.through,
    Mission.target_satellites.through,
):
    m2m_changed.connect(
        on_m2m_change,
        sender=through_model,
        dispatch_uid=f"cache-m2m-{through_model.__name__}",
    )
