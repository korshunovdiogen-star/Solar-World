from django.shortcuts import render
from functools import wraps
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import date
from django.shortcuts import render, get_object_or_404
from .models import Planet, Satellite, Mission, SpaceAgency, Company
from rest_framework import serializers
from rest_framework import viewsets
from solarWorld.serializers import (
    PlanetSerializer, SatelliteSerializer,
    MissionSerializer, SpaceAgencySerializer,
    CompanySerializer
)
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from users.models import History, Favorite
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from users.decorators import track_user_activity
from .utils import separate_first_line
from django.core.paginator import Paginator
from django.http import JsonResponse



# Главная страница
@cache_page(60 * 15)
def main(request):
    return render(request, 'planets/main.html')

# Список всех планет
def planet_list(request):
    planets = Planet.objects.all()
    return render(request, 'planets/planet_list.html', {'planets': planets})

# Страница планеты
@track_user_activity(Planet)
def planet_detail(request, pk, is_favorite=False):
    cache_key = f"planet:{pk}:detail"
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'planets/planet_detail.html', cached_context)

    planet = get_object_or_404(Planet, pk=pk)

    first_line, remaining_text = separate_first_line(planet);

    satellites = planet.satellites.all().order_by('satellite_type', 'name') 

    context = {
        'planet': planet, #сам объект
        'satellites': satellites,# список объектов спутников 
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
        'is_favorite': is_favorite,
        'content_type': 'planet', # используется в кнопке избранного
    }
    cache.set(cache_key, context, timeout=60 * 15)
    return render(request, 'planets/planet_detail.html', context)

# Страница конкретного спутника
@track_user_activity(Satellite)
def satellite_detail(request, pk, is_favorite=False):
    cache_key = f"satellite:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        return render(request, 'planets/satellite_detail.html', cached_context)

    satellite = get_object_or_404(Satellite, pk=pk)

    first_line, remaining_text = separate_first_line(satellite); 

    context={   
        'satellite': satellite,
        'first_line': first_line,
        'remaining_text': remaining_text, 
        'is_favorite': is_favorite,
        'content_type': 'satellite',
        }
    cache.set(cache_key, context, timeout=60 * 15)
    return render(request, 'planets/satellite_detail.html', context)


@track_user_activity(Mission)
def mission_detail(request, pk, is_favorite=False):
    cache_key = f"mission:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        return render(request, 'planets/mission_detail.html', cached_context)

    mission = get_object_or_404(Mission, pk=pk)

    first_line, remaining_text = separate_first_line(mission); 

    duration = (timezone.now().date() - mission.launch_date).days 

    context={
        'mission': mission, 
        'first_line': first_line,
        'remaining_text': remaining_text, 
        'duration': duration,
        'is_favorite': is_favorite,
        'content_type': 'mission', 
    }
    cache.set(cache_key, context, timeout=60 * 15)
    return render(request, 'planets/mission_detail.html', context)


@track_user_activity(SpaceAgency)
def spaceAgency_detail(request, pk, is_favorite=False):
    cache_key = f"spaceAgency:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        return render(request, 'planets/spaceAgency_detail.html', cached_context)

    spaceAgency = get_object_or_404(SpaceAgency, pk=pk)

    first_line, remaining_text = separate_first_line(spaceAgency);  
    days_passed=date.today()-spaceAgency.established_date

    context={
        'spaceAgency': spaceAgency, 
        'first_line': first_line, 
        'remaining_text': remaining_text,
        'days_passed': days_passed.days,
        'is_favorite': is_favorite,
        'content_type': 'spaceAgency',
        }
    cache.set(cache_key, context, timeout=60 * 15)
    return render(request, 'planets/spaceAgency_detail.html', context)


@track_user_activity(Company)
def company_detail(request, pk, is_favorite=False):
    cache_key = f"company:{pk}:detail"
    cached_context = cache.get(cache_key)

    if cached_context is not None:
        return render(request, 'planets/company_detail.html', cached_context)

    company = get_object_or_404(Company, pk=pk)

    first_line, remaining_text = separate_first_line(company);  
    days_passed=date.today()-company.established_date

    context={
        'company': company,
        'first_line': first_line,
        'remaining_text': remaining_text,
        'days_passed': days_passed.days, #сколько дней прошло со дня основания
        'content_type': 'company',
    }
    cache.set(cache_key, context, timeout=60 * 15)
    return render(request, 'planets/company_detail.html', context)






def catalog_page(request):
    return render(request, 'planets/catalog.html')

SORT_MAP = {
    'all': {'name_asc': 'name', 'name_desc': '-name'},
    'planet': {'name_asc': 'name', 'name_desc': '-name', 
               'radius_asc': 'radius', 'radius_desc': '-radius',
               'type_asc' : 'planet_type', 'type_desc' : '-planet_type'},
    'satellite': {'name_asc': 'name', 'name_desc': '-name',
                  'radius_asc': 'radius', 'radius_desc': '-radius',
                  'type_asc' : 'satellite_type', 'type_desc' : '-satellite_type'},
    'mission': {'name_asc': 'name', 'name_desc': '-name',
                'mission_type_asc': 'mission_type','mission_type_desc': '-mission_type',
                'agency_asc': 'space_agency__name', 'agency_desc': '-space_agency__name'},
    'agency': {'name_asc': 'name', 'name_desc': '-name'},
    'company': {'name_asc': 'name', 'name_desc': '-name',
                'revenue_asc': 'revenue_2025', 'revenue_desc': '-revenue_2025',
                'country_asc' : 'country', 'country_desc' : '-country'},
}

@cache_page(60 * 15)
def catalog_api(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    ordering = request.GET.get('ordering', 'name_asc')
    page = int(request.GET.get('page', 1))
    per_page = 12

    page = max(1, page) # Защита от некорректного номера страницы
    results = []
    total_pages = 1




    if category == 'all':
        MAX_FOR_ALL = 25
        all_results = []

        try:
            planets = Planet.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += PlanetSerializer(planets, many=True).data
        except Exception as e:
            print(f"Ошибка в планетах: {e}")

        try:
            satellites = Satellite.objects.filter(name__icontains=q).select_related('planet')[:MAX_FOR_ALL]
            all_results += SatelliteSerializer(satellites, many=True).data
        except Exception as e:
            print(f"Ошибка в спутниках: {e}")

        try:
            missions = Mission.objects.filter(name__icontains=q).prefetch_related('agencies')[:MAX_FOR_ALL]
            all_results += MissionSerializer(missions, many=True).data
        except Exception as e:
            print(f"Ошибка в миссиях: {e}")

        try:
            agencies = SpaceAgency.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += SpaceAgencySerializer(agencies, many=True).data
        except Exception as e:
            print(f"Ошибка в агентствах: {e}")

        try:
            companies = Company.objects.filter(name__icontains=q)[:MAX_FOR_ALL]
            all_results += CompanySerializer(companies, many=True).data
        except Exception as e:
            print(f"Ошибка в компаниях: {e}")

        # Сортировка объединённого списка
        if ordering in ('name_asc', 'name_desc'):
            all_results.sort(key=lambda x: x.get('name', ''), reverse=(ordering == 'name_desc'))

        paginator = Paginator(all_results, per_page)
        page_obj = paginator.get_page(page)
        results = page_obj.object_list
        total_pages = paginator.num_pages
        # ========== КОНКРЕТНАЯ КАТЕГОРИЯ ==========
    else:
        model_map = {
            'planet': (Planet, PlanetSerializer, 'planet'),
            'satellite': (Satellite, SatelliteSerializer, 'satellite'),
            'mission': (Mission, MissionSerializer, 'mission'),
            'agency': (SpaceAgency, SpaceAgencySerializer, 'agency'),
            'company': (Company, CompanySerializer, 'company'),
        }

        if category in model_map:
            model, serializer_class, model_type = model_map[category]
            try:
                queryset = model.objects.filter(name__icontains=q)

                # Оптимизации для связанных полей
                if category == 'satellite':
                    queryset = queryset.select_related('planet')
                elif category == 'mission':
                    queryset = queryset.prefetch_related('agencies')

                sort_field = SORT_MAP.get(category, {}).get(ordering, 'id')
                queryset = queryset.order_by(sort_field)

                total_count = queryset.count()
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                page = min(page, total_pages)
                offset = (page - 1) * per_page

                items = queryset[offset:offset + per_page]
                results = serializer_class(items, many=True).data

            except Exception as e:
                print(f"Ошибка в {category}: {e}")
                results = []
                total_pages = 1
        else:
            # Неизвестная категория
            results = []
            total_pages = 1
            
    


    return JsonResponse({
        'results': results,
        'total_pages': total_pages,
        'current_page': page,
    })






# API
class PlanetViewSet(viewsets.ModelViewSet):
    queryset = Planet.objects.all()
    serializer_class = PlanetSerializer

class SatelliteViewSet(viewsets.ModelViewSet):
    queryset = Satellite.objects.all()
    serializer_class = SatelliteSerializer

class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

class SpaceAgencyViewSet(viewsets.ModelViewSet):
    queryset = SpaceAgency.objects.all()
    serializer_class = SpaceAgencySerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer