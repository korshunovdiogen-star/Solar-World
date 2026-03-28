from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Planet, Satellite


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
    first_line = planet.planet_text.splitlines()[0] if planet.planet_text else ''
    lines = planet.planet_text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    # Если в ForeignKey у Satellite нет related_name, пишем planet.satellite_set.all()
    satellites = planet.satellites.all().order_by('satellite_type', 'satellite_name') 
    return render(request, 'planets/planet_detail.html', {
        'planet': planet, #сам объект
        'satellites': satellites,# список объектов спутников 
        'first_line': first_line, # Первая строка описания (подзаголовок)
        'remaining_text': remaining_text, # текст описания без первой строки
    })

# Страница конкретного спутника
def satellite_detail(request, pk):
    satellite = get_object_or_404(Satellite, pk=pk)
    return render(request, 'planets/satellite_detail.html', {'satellite': satellite})

