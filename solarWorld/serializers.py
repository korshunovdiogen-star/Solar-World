from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from planets.models import Company, Mission, Planet, Satellite, SpaceAgency

_CATALOG_DETAIL_URLS = {
    "planet": "planet_detail",
    "satellite": "satellite_detail",
    "mission": "mission_detail",
    "spaceagency": "spaceagency_detail",
    "company": "company_detail",
}


def _first_line(text):
    if not text:
        return ""
    lines = text.splitlines()
    return lines[0] if lines else ""


class CatalogCardSerializer(serializers.Serializer):
    """Лёгкая карточка каталога без полного text и вложенных объектов."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    model_type = serializers.SerializerMethodField()
    first_line = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    radius = serializers.FloatField(read_only=True)
    country = serializers.CharField(read_only=True)
    annual_revenue = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )
    agency_names = serializers.SerializerMethodField()

    def get_model_type(self, obj) -> str:
        return obj._meta.model_name

    def get_first_line(self, obj) -> str:
        return _first_line(getattr(obj, "text", None))

    def get_image(self, obj) -> str | None:
        image = getattr(obj, "image", None)
        if not image:
            return None
        try:
            return image.url
        except ValueError:
            return None

    def get_detail_url(self, obj) -> str | None:
        url_name = _CATALOG_DETAIL_URLS.get(obj._meta.model_name)
        if not url_name:
            return None
        return reverse(url_name, args=[obj.pk])

    def get_type_display(self, obj) -> str:
        for method_name in (
            "get_planet_type_display",
            "get_satellite_type_display",
            "get_mission_type_display",
        ):
            method = getattr(obj, method_name, None)
            if method is not None:
                return method()
        return ""

    def get_agency_names(self, obj) -> list[str]:
        agencies = getattr(obj, "space_agency", None)
        if agencies is None:
            return []
        return [agency.name for agency in agencies.all()]


class PlanetSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    satellites = serializers.StringRelatedField(many=True, read_only=True)
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_planet_type_display", read_only=True)

    class Meta:
        model = Planet
        fields = [
            "id",
            "name",
            "radius",
            "image",
            "text",
            "model_type",
            "detail_url",
            "first_line",
            "remaining_text",
            "satellites",
            "type_display",
        ]

    def get_first_line(self, obj) -> str:
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj) -> str:
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj) -> str:
        return "planet"

    def get_detail_url(self, obj) -> str:
        from django.urls import reverse

        return reverse("planet_detail", args=[obj.id])


class SatelliteSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_satellite_type_display", read_only=True)

    class Meta:
        model = Satellite
        fields = [
            "id",
            "name",
            "radius",
            "image",
            "text",
            "planet",
            "detail_url",
            "first_line",
            "remaining_text",
            "model_type",
            "type_display",
        ]

    def get_first_line(self, obj) -> str:
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj) -> str:
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj) -> str:
        return "satellite"

    def get_detail_url(self, obj) -> str:
        from django.urls import reverse

        return reverse("satellite_detail", args=[obj.id])


class MissionSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_mission_type_display", read_only=True)
    agency_names = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id",
            "name",
            "launch_date",
            "image",
            "detail_url",
            "status",
            "target_planets",
            "target_satellites",
            "text",
            "agency_names",
            "first_line",
            "remaining_text",
            "duration",
            "model_type",
            "type_display",
        ]

    def get_first_line(self, obj) -> str:
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj) -> str:
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_duration(self, obj) -> int | None:
        if obj.launch_date:
            return (timezone.now().date() - obj.launch_date).days
        return None

    def get_model_type(self, obj) -> str:
        return "mission"

    def get_detail_url(self, obj) -> str:
        from django.urls import reverse

        return reverse("mission_detail", args=[obj.id])

    def get_agency_names(self, obj) -> list[str]:
        return [agency.name for agency in obj.space_agency.all()]


class SpaceAgencySerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    days_passed = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    country = serializers.CharField(read_only=True)

    class Meta:
        model = SpaceAgency
        fields = [
            "id",
            "name",
            "country",
            "established_date",
            "image",
            "detail_url",
            "text",
            "first_line",
            "remaining_text",
            "days_passed",
            "model_type",
        ]

    def get_first_line(self, obj) -> str:
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj) -> str:
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_days_passed(self, obj) -> int | None:
        if obj.established_date:
            return (timezone.now().date() - obj.established_date).days
        return None

    def get_model_type(self, obj) -> str:
        return "spaceagency"

    def get_detail_url(self, obj) -> str:
        from django.urls import reverse

        return reverse("spaceagency_detail", args=[obj.id])


class CompanySerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "country",
            "established_date",
            "founders",
            "image",
            "text",
            "headquarters",
            "employees",
            "ceo",
            "annual_revenue",
            "first_line",
            "remaining_text",
            "model_type",
            "detail_url",
        ]

    def get_first_line(self, obj) -> str:
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj) -> str:
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj) -> str:
        return "company"

    def get_detail_url(self, obj) -> str:
        from django.urls import reverse

        return reverse("company_detail", args=[obj.id])
