import logging
from datetime import date

from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from rest_framework import viewsets

from solarWorld.serializers import (
    CatalogCardSerializer,
    CompanySerializer,
    MissionSerializer,
    PlanetSerializer,
    SatelliteSerializer,
    SpaceAgencySerializer,
)
from solarWorld.utils import parse_page_number
from users.decorators import track_user_activity

from .models import Company, Mission, Planet, Satellite, SpaceAgency
from .utils import (
    get_daily_planet_from_microservice,
    get_daily_planet_thumbnail,
    seconds_until_midnight,
    separate_first_line,
)

logger = logging.getLogger(__name__)


def main(request):
    planet = get_daily_planet_from_microservice()
    first_line = ""
    if planet and planet.text:
        lines = planet.text.split("\n", 1)
        first_line = lines[0] if lines else ""

    context = {
        "daily_planet": planet,
        "daily_first_line": first_line,
    }
    return render(request, "planets/main.html", context)


def planet_list(request):
    planets = Planet.objects.all()
    return render(request, "planets/planet_list.html", {"planets": planets})


@track_user_activity(Planet)
def planet_detail(request, pk, is_favorite=False):
    cache_key = f"planet:{pk}:detail"
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        context = dict(cached_context)
        context["is_favorite"] = is_favorite
        return render(request, "planets/planet_detail.html", context)

    planet = get_object_or_404(Planet, pk=pk)

    first_line, remaining_text = separate_first_line(planet)

    satellites = planet.satellites.all().order_by("satellite_type", "name")

    context = {
        "planet": planet,  # сам объект
        "satellites": satellites,  # список объектов спутников
        "first_line": first_line,  # Первая строка описания (подзаголовок)
        "remaining_text": remaining_text,  # текст описания без первой строки
        "is_favorite": is_favorite,  # является ли избранным
        "content_type": "planet",  # используется в кнопке избранного
    }
    context.pop("is_favorite", None)
    cache.set(cache_key, context, timeout=60 * 15)

    context = dict(context)
    context["is_favorite"] = is_favorite
    return render(request, "planets/planet_detail.html", context)


@track_user_activity(Satellite)
def satellite_detail(request, pk, is_favorite=False):
    cache_key = f"satellite:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        context = dict(cached_context)
        context["is_favorite"] = is_favorite
        return render(request, "planets/satellite_detail.html", context)

    satellite = get_object_or_404(Satellite, pk=pk)

    first_line, remaining_text = separate_first_line(satellite)

    context = {
        "satellite": satellite,
        "first_line": first_line,
        "remaining_text": remaining_text,
        "is_favorite": is_favorite,
        "content_type": "satellite",
    }
    context.pop("is_favorite", None)
    cache.set(cache_key, context, timeout=60 * 15)

    context = dict(context)
    context["is_favorite"] = is_favorite
    return render(request, "planets/satellite_detail.html", context)


@track_user_activity(Mission)
def mission_detail(request, pk, is_favorite=False):
    cache_key = f"mission:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        context = dict(cached_context)
        context["is_favorite"] = is_favorite
        return render(request, "planets/mission_detail.html", context)

    mission = get_object_or_404(Mission, pk=pk)

    first_line, remaining_text = separate_first_line(mission)

    duration = (timezone.now().date() - mission.launch_date).days

    context = {
        "mission": mission,
        "first_line": first_line,
        "remaining_text": remaining_text,
        "duration": duration,
        "is_favorite": is_favorite,
        "content_type": "mission",
    }
    context.pop("is_favorite", None)
    cache.set(cache_key, context, timeout=60 * 15)

    context = dict(context)
    context["is_favorite"] = is_favorite
    return render(request, "planets/mission_detail.html", context)


@track_user_activity(SpaceAgency)
def spaceAgency_detail(request, pk, is_favorite=False):
    cache_key = f"spaceAgency:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        context = dict(cached_context)
        context["is_favorite"] = is_favorite
        return render(request, "planets/spaceAgency_detail.html", context)

    spaceAgency = get_object_or_404(SpaceAgency, pk=pk)

    first_line, remaining_text = separate_first_line(spaceAgency)
    days_passed = date.today() - spaceAgency.established_date

    context = {
        "spaceAgency": spaceAgency,
        "first_line": first_line,
        "remaining_text": remaining_text,
        "days_passed": days_passed.days,
        "is_favorite": is_favorite,
        "content_type": "spaceAgency",
    }
    context.pop("is_favorite", None)
    cache.set(cache_key, context, timeout=60 * 15)

    context = dict(context)
    context["is_favorite"] = is_favorite
    return render(request, "planets/spaceAgency_detail.html", context)


@track_user_activity(Company)
def company_detail(request, pk, is_favorite=False):
    cache_key = f"company:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        context = dict(cached_context)
        context["is_favorite"] = is_favorite
        return render(request, "planets/company_detail.html", context)

    company = get_object_or_404(Company, pk=pk)

    first_line, remaining_text = separate_first_line(company)
    days_passed = date.today() - company.established_date

    context = {
        "company": company,
        "first_line": first_line,
        "remaining_text": remaining_text,
        "days_passed": days_passed.days,  # сколько дней прошло со дня основания
        "content_type": "company",
    }
    # is_favorite у каждого пользователя свой, поэтому в общий кеш его не кладём.
    context.pop("is_favorite", None)
    cache.set(cache_key, context, timeout=60 * 15)

    context = dict(context)
    context["is_favorite"] = is_favorite
    return render(request, "planets/company_detail.html", context)


def catalog_page(request):
    return render(request, "planets/content_catalog.html")


SORT_MAP = {
    "all": {"name_asc": "name", "name_desc": "-name"},
    "planet": {
        "name_asc": "name",
        "name_desc": "-name",
        "radius_asc": "radius",
        "radius_desc": "-radius",
        "type_asc": "planet_type",
        "type_desc": "-planet_type",
    },
    "satellite": {
        "name_asc": "name",
        "name_desc": "-name",
        "radius_asc": "radius",
        "radius_desc": "-radius",
        "type_asc": "satellite_type",
        "type_desc": "-satellite_type",
    },
    "mission": {
        "name_asc": "name",
        "name_desc": "-name",
        "mission_type_asc": "mission_type",
        "mission_type_desc": "-mission_type",
        "agency_asc": "space_agency__name",
        "agency_desc": "-space_agency__name",
    },
    "agency": {"name_asc": "name", "name_desc": "-name"},
    "company": {
        "name_asc": "name",
        "name_desc": "-name",
        "revenue_asc": "annual_revenue",
        "revenue_desc": "-annual_revenue",
        "country_asc": "country",
        "country_desc": "-country",
    },
}


@cache_page(60 * 15)
def catalog_api(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "all")
    ordering = request.GET.get("ordering", "name_asc")
    page = parse_page_number(request.GET.get("page", 1))
    per_page = 12

    page = max(1, page)  # Защита от некорректного номера страницы
    results = []
    total_pages = 1

    if category == "all":
        MAX_FOR_ALL = 25
        all_results = []

        try:
            planets = Planet.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += CatalogCardSerializer(planets, many=True).data
        except Exception:
            logger.exception("Не удалось сериализовать планеты в общем каталоге")

        try:
            satellites = Satellite.objects.filter(name__icontains=q).select_related("planet")[
                :MAX_FOR_ALL
            ]
            all_results += CatalogCardSerializer(satellites, many=True).data
        except Exception:
            logger.exception("Не удалось сериализовать спутники в общем каталоге")

        try:
            missions = Mission.objects.filter(name__icontains=q).prefetch_related("space_agency")[
                :MAX_FOR_ALL
            ]
            all_results += CatalogCardSerializer(missions, many=True).data
        except Exception:
            logger.exception("Не удалось сериализовать миссии в общем каталоге")

        try:
            agencies = SpaceAgency.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += CatalogCardSerializer(agencies, many=True).data
        except Exception:
            logger.exception("Не удалось сериализовать агентства в общем каталоге")

        try:
            companies = Company.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += CatalogCardSerializer(companies, many=True).data
        except Exception:
            logger.exception("Не удалось сериализовать компании в общем каталоге")

        # Сортировка объединённого списка
        if ordering in ("name_asc", "name_desc"):
            all_results.sort(key=lambda x: x.get("name", ""), reverse=(ordering == "name_desc"))

        paginator = Paginator(all_results, per_page)
        page_obj = paginator.get_page(page)
        results = page_obj.object_list
        total_pages = paginator.num_pages
        # ========== КОНКРЕТНАЯ КАТЕГОРИЯ ==========
    else:
        model_map = {
            "planet": Planet,
            "satellite": Satellite,
            "mission": Mission,
            "agency": SpaceAgency,
            "company": Company,
        }

        if category in model_map:
            model = model_map[category]
            try:
                queryset = model.objects.filter(name__icontains=q)

                # Оптимизации для связанных полей
                if category == "satellite":
                    queryset = queryset.select_related("planet")
                elif category == "mission":
                    queryset = queryset.prefetch_related("space_agency")

                sort_field = SORT_MAP.get(category, {}).get(ordering, "id")
                queryset = queryset.order_by(sort_field)

                total_count = queryset.count()
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                page = min(page, total_pages)
                offset = (page - 1) * per_page

                items = queryset[offset : offset + per_page]
                results = CatalogCardSerializer(items, many=True).data

            except Exception:
                logger.exception("Ошибка при выборке категории %s", category)
                results = []
                total_pages = 1
        else:
            # Неизвестная категория
            results = []
            total_pages = 1

    return JsonResponse(
        {
            "results": results,
            "total_pages": total_pages,
            "current_page": page,
        }
    )


def planet_of_the_day(request):
    planet = get_daily_planet_from_microservice()
    if planet is None:
        return redirect("main")
    return redirect("planet_detail", pk=planet.id)


def planet_of_the_day_thumbnail(request):
    """
    Отдаёт уменьшенную картинку планеты дня.

    Миниатюра генерируется один раз в сутки и лежит в кеше до полуночи,
    поэтому карточка на главной не тянет полноразмерный файл (сотни КБ),
    а новые файлы на диске не создаются. При ошибке — отдаём оригинал.
    """
    planet = get_daily_planet_from_microservice()

    if planet is None or not planet.image:
        raise Http404("Планета дня не найдена")

    data = get_daily_planet_thumbnail(planet)
    if data is None:
        return redirect(planet.image.url)

    response = HttpResponse(data, content_type="image/webp")
    response["Cache-Control"] = f"public, max-age={seconds_until_midnight()}"
    response["ETag"] = f'"{planet.pk}-{timezone.localdate().isoformat()}"'
    return response


# API
class PlanetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Planet.objects.all()
    serializer_class = PlanetSerializer


class SatelliteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Satellite.objects.all()
    serializer_class = SatelliteSerializer


class MissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer


class SpaceAgencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SpaceAgency.objects.all()
    serializer_class = SpaceAgencySerializer


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
