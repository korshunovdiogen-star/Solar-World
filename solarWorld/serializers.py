from rest_framework import serializers
from planets.models import Planet, Satellite, Mission, SpaceAgency
from django.utils import timezone
from datetime import date

class PlanetSerializer(serializers.ModelSerializer):
    # Дополнительные поля для API
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    # Вложенный список спутников (опционально)
    satellites = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Planet
        fields = [
            'id', 'name', 'radius', 'type', 'description',
            'image', 'interesting_fact', 'text',
            'first_line', 'remaining_text', 'satellites'
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

class SatelliteSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    # Можно добавить название планеты для удобства
    planet_name = serializers.CharField(source='planet.name', read_only=True)

    class Meta:
        model = Satellite
        fields = [
            'id', 'name', 'radius', 'type', 'description',
            'image', 'text', 'planet', 'planet_name',
            'first_line', 'remaining_text'
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

class MissionSerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()  # дней со дня запуска

    class Meta:
        model = Mission
        fields = [
            'id', 'name', 'agency', 'mission_type', 'launch_date',
            'status', 'target', 'description', 'text',
            'first_line', 'remaining_text', 'duration'
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

class SpaceAgencySerializer(serializers.ModelSerializer):
    first_line = serializers.SerializerMethodField()
    remaining_text = serializers.SerializerMethodField()
    days_passed = serializers.SerializerMethodField()

    class Meta:
        model = SpaceAgency
        fields = [
            'id', 'name', 'country', 'established_date', 'description',
            'text', 'first_line', 'remaining_text', 'days_passed'
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
            return (date.today() - obj.established_date).days
        return None








# class SpaceAgencySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SpaceAgency
#         fields = '__all__'

# class SatelliteSerializer(serializers.ModelSerializer):
#     # Добавляем человекочитаемое название типа (get_..._display)
#     satellite_type_display = serializers.CharField(source='get_satellite_type_display', read_only=True)

#     class Meta:
#         model = Satellite
#         fields = '__all__'

# class PlanetSerializer(serializers.ModelSerializer):
#     planet_type_display = serializers.CharField(source='get_planet_type_display', read_only=True)
#     # Позволяет видеть список спутников внутри JSON-а планеты
#     satellites = SatelliteSerializer(many=True, read_only=True)

#     class Meta:
#         model = Planet
#         fields = [
#             'id', 'name', 'orger', 'planet_type', 'planet_type_display', 
#             'radius', 'text', 'image', 'satellites'
#         ]

# class MissionSerializer(serializers.ModelSerializer):
#     mission_type_display = serializers.CharField(source='get_mission_type_display', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
    
#     # Для ManyToMany полей можно выводить только ID (по умолчанию) 
#     # или сделать их вложенными, если нужно подробнее
#     class Meta:
#         model = Mission
#         fields = '__all__'