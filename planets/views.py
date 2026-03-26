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

# Страница планеты и её спутников
def planet_detail(request, pk):
    planet = get_object_or_404(Planet, pk=pk)
    # Если в ForeignKey у Satellite нет related_name, пишем planet.satellite_set.all()
    satellites = planet.satellites.all() 
    return render(request, 'planets/planet_detail.html', {
        'planet': planet, 
        'satellites': satellites
    })

# Страница конкретного спутника
def satellite_detail(request, pk):
    satellite = get_object_or_404(Satellite, pk=pk)
    return render(request, 'planets/satellite_detail.html', {'satellite': satellite})

