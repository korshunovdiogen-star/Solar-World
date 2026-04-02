from django.shortcuts import render
from django.utils import timezone
from datetime import date
from django.shortcuts import render, get_object_or_404
from .models import Planet, Satellite, Mission, SpaceAgency
from rest_framework import serializers
from rest_framework import viewsets
from solarWorld.serializers import (
    PlanetSerializer, SatelliteSerializer,
    MissionSerializer, SpaceAgencySerializer
)
from django.core.paginator import Paginator
from django.http import JsonResponse


# Главная страница
def main(request):
    return render(request, 'planets/main.html')

# Список всех планет
def planet_list(request):
    planets = Planet.objects.all()
    return render(request, 'planets/planet_list.html', {'planets': planets})

# Страница планеты
def planet_detail(request, pk):
    planet = get_object_or_404(Planet, pk=pk)
    first_line = planet.text.splitlines()[0] if planet.text else ''
    lines = planet.text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    satellites = planet.satellites.all().order_by('satellite_type', 'name') 
    return render(request, 'planets/planet_detail.html', {
        'planet': planet, #сам объект
        'satellites': satellites,# список объектов спутников 
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
    })

# Страница конкретного спутника
def satellite_detail(request, pk):
    satellite = get_object_or_404(Satellite, pk=pk)
    first_line = satellite.text.splitlines()[0] if satellite.text else ''
    lines = satellite.text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    return render(request, 'planets/satellite_detail.html', {
        'satellite': satellite,
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
        })


def mission_detail(request, pk):
    mission = get_object_or_404(Mission, pk=pk)
    first_line = mission.text.splitlines()[0] if mission.text else ''
    lines = mission.text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    duration = (timezone.now().date() - mission.launch_date).days # кол-во дней со здня запуска

    return render(request, 'planets/mission_detail.html', {
        'mission': mission, #сам объект 
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
        'duration': duration,
    })

def spaceAgency_detail(request, pk):
    spaceAgency = get_object_or_404(SpaceAgency, pk=pk)
    first_line = spaceAgency.text.splitlines()[0] if spaceAgency.text else ''
    lines = spaceAgency.text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    days_passed=date.today()-spaceAgency.established_date

    return render(request, 'planets/spaceAgency_detail.html', {
        'spaceAgency': spaceAgency, #сам объект 
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
        'days_passed': days_passed.days #сколько дней прошло со дня основания
    })




def catalog_page(request):
    return render(request, 'planets/catalog.html')

def catalog_api(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    page = int(request.GET.get('page', 1)) # номер страницы
    per_page = 12  # количество объектов на странице

    results = []
    # Собираем объекты в зависимости от категории
    if category in ('all', 'planet'):
        planets = Planet.objects.filter(name__icontains=q)
        results += PlanetSerializer(planets, many=True).data
    if category in ('all', 'satellite'):
        satellites = Satellite.objects.filter(name__icontains=q)
        results += SatelliteSerializer(satellites, many=True).data
    if category in ('all', 'mission'):
        missions = Mission.objects.filter(name__icontains=q)
        results += MissionSerializer(missions, many=True).data
    if category in ('all', 'agency'):
        agencies = SpaceAgency.objects.filter(name__icontains=q)
        results += SpaceAgencySerializer(agencies, many=True).data

    paginator = Paginator(results, per_page)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'results': page_obj.object_list,
        'total_pages': paginator.num_pages,
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