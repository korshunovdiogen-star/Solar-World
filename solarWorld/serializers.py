from rest_framework import serializers
from planets.models import Planet, Satellite, Mission, SpaceAgency, Company
from django.utils import timezone
from datetime import date

class PlanetSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    satellites = serializers.StringRelatedField(many=True, read_only=True)
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_planet_type_display', read_only=True)

    class Meta:
        model = Planet
        fields = [
            'id', 'name', 'radius',
            'image', 'text', 'model_type', 'detail_url',
            'first_line', 'remaining_text', 'satellites', 'type_display'
        ]

    def get_first_line(self, obj):
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj):
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj):
        return 'planet' 

    def get_detail_url(self, obj):
        from django.urls import reverse
        return reverse('planet_detail', args=[obj.id]) 


class SatelliteSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_satellite_type_display', read_only=True)

    class Meta:
        model = Satellite
        fields = [
            'id', 'name', 'radius',
            'image', 'text', 'planet', 'detail_url',
            'first_line', 'remaining_text', 'model_type', 'type_display'
        ]

    def get_first_line(self, obj):
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj):
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj):
        return 'satellite' 

    def get_detail_url(self, obj):
        from django.urls import reverse
        return reverse('satellite_detail', args=[obj.id]) 


class MissionSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_mission_type_display', read_only=True)
    agency_names = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            'id', 'name', 'launch_date', 'image', 'detail_url',
            'status', 'target_planets', 'target_satellites', 'text', 'agency_names',
            'first_line', 'remaining_text', 'duration', 'model_type', 'type_display'
        ]

    def get_first_line(self, obj):
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj):
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_duration(self, obj):
        if obj.launch_date:
            return (timezone.now().date() - obj.launch_date).days
        return None

    def get_model_type(self, obj):
        return 'mission' 

    def get_detail_url(self, obj):
        from django.urls import reverse
        return reverse('mission_detail', args=[obj.id]) 

    def get_agency_names(self, obj):
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
            'id', 'name', 'country', 'established_date', 'image', 'detail_url',
            'text', 'first_line', 'remaining_text', 'days_passed', 'model_type',
        ]

    def get_first_line(self, obj):
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj):
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_days_passed(self, obj):
        if obj.established_date:
            return (timezone.now().date() - obj.established_date).days
        return None

    def get_model_type(self, obj):
        return 'spaceagency' 

    def get_detail_url(self, obj):
        from django.urls import reverse
        return reverse('spaceagency_detail', args=[obj.id]) 


class CompanySerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    model_type = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'country', 'established_date', 'founders', 'image', 'text',
            'headquarters', 'employees', 'CEO', 'revenue_2025',
            'first_line', 'remaining_text', 'model_type', 'detail_url'
        ]

    def get_first_line(self, obj):
        if obj.text:
            return obj.text.splitlines()[0]
        return ""

    def get_remaining_text(self, obj):
        if obj.text:
            lines = obj.text.splitlines()
            return "\n".join(lines[1:])
        return ""

    def get_model_type(self, obj):
        return 'company'

    def get_detail_url(self, obj):
        from django.urls import reverse
        return reverse('company_detail', args=[obj.id])
