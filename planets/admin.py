from django.contrib import admin
from .models import Planet
from .models import Satellite



class PlanetsAdmin(admin.ModelAdmin):
    list_display = ['planet_name', 'planet_orger', 'planet_type', 'planet_radius']

class SatelliteAdmin(admin.ModelAdmin):
    list_display = ['satellite_name', 'planet', 'satellite_type', 'satellite_radius']


admin.site.register(Planet, PlanetsAdmin)
admin.site.register(Satellite, SatelliteAdmin)