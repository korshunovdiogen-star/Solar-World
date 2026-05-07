from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Planet, Satellite, Mission, SpaceAgency, Company

def invalidate_detail_cache(model_name, pk):
    cache_key = f"{model_name}:{pk}:detail"
    cache.delete(cache_key)

def invalidate_catalog_and_main():
    cache.delete_pattern("*catalog*")
    cache.delete("main_page")

def handle_model_change(sender, instance, **kwargs):
    model_name = sender.__name__.lower()

    invalidate_detail_cache(model_name, instance.pk)

    if model_name == 'satellite' and instance.planet:
        invalidate_detail_cache('planet', instance.planet.pk)

    if model_name == 'mission':
        for agency in instance.agencies.all():
            invalidate_detail_cache('agency', agency.pk)
        if hasattr(instance, 'planet') and instance.planet:
            invalidate_detail_cache('planet', instance.planet.pk)

    invalidate_catalog_and_main()

    print(f"Кеш {model_name} #{instance.pk}, каталога и главной сброшен.")

MODELS_TO_WATCH = [Planet, Satellite, Mission, SpaceAgency, Company]

@receiver(post_save, sender=MODELS_TO_WATCH)
def on_model_save(sender, instance, **kwargs):
    handle_model_change(sender, instance, **kwargs)

@receiver(post_delete, sender=MODELS_TO_WATCH)
def on_model_delete(sender, instance, **kwargs):
    handle_model_change(sender, instance, **kwargs)