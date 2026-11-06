from django.contrib import admin

from .forms import MissionAdminForm
from .models import Company, Mission, Planet, Satellite, SpaceAgency


class PlanetsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "planet_type", "radius"]


class SatelliteAdmin(admin.ModelAdmin):
    list_display = ["name", "planet", "satellite_type", "radius"]


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "display_space_agencies",
        "get_mission_type_display",
        "launch_date",
        "success",
        "get_targets_display",
    ]
    list_filter = ["mission_type", "success", "space_agency"]
    search_fields = ["name", "description"]
    filter_horizontal = ["target_planets", "target_satellites", "space_agency"]
    form = MissionAdminForm

    def get_targets_display(self, obj):
        targets = []
        if obj.target_planets.exists():
            targets.extend(
                [f"Планета: {planet.planet_name}" for planet in obj.target_planets.all()]
            )
        if obj.target_satellites.exists():
            targets.extend(
                [f"Спутник: {sat.satellite_name}" for sat in obj.target_satellites.all()]
            )
        return ", ".join(targets) or "Цели не указаны"

    get_targets_display.short_description = "Цели"


class SpaceAgencyAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "established_date"]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "established_date", "employees", "CEO")
    search_fields = ("name", "country")
    list_filter = ("country",)


admin.site.register(Planet, PlanetsAdmin)
admin.site.register(Satellite, SatelliteAdmin)
admin.site.register(SpaceAgency, SpaceAgencyAdmin)
