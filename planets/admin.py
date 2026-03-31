from django.contrib import admin
from django import forms
from .forms import MissionAdminForm
from .models import Planet, Mission, SpaceAgency, Satellite



class PlanetsAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'planet_type', 'radius']

class SatelliteAdmin(admin.ModelAdmin):
    list_display = ['name', 'planet', 'satellite_type', 'radius']

class MissionAdmin(admin.ModelAdmin):
    list_display = [
        'name',                 # Название
        'display_space_agencies',       # Агентства
        'get_mission_type_display',     # Тип 
        'launch_date',                  # Дата запуска
        'success',                      # Успех/неуспех
        'get_targets_display',          # Цели (планеты и спутники)
    ]

    def get_targets_display(self, obj):
        targets = []
        if obj.target_planets.exists():
            targets.extend([f'Планета: {planet.planet_name}' for planet in obj.target_planets.all()])
        if obj.target_satellites.exists():
            targets.extend([f'Спутник: {sat.satellite_name}' for sat in obj.target_satellites.all()])
        return ', '.join(targets) or 'Цели не указаны'
    get_targets_display.short_description = 'Цели'


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
        list_filter = ['mission_type', 'success', 'space_agency']
        search_fields = ['name', 'description']
        filter_horizontal = ['target_planets', 'target_satellites', 'space_agency']
        form = MissionAdminForm

class SpaceAgencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'established_date']


admin.site.register(Planet, PlanetsAdmin)
admin.site.register(Satellite, SatelliteAdmin)
admin.site.register(SpaceAgency, SpaceAgencyAdmin)