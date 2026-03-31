from django.db import models
from django.utils import timezone


class Planet(models.Model):
    class PlanetType(models.TextChoices):
        TERRESTRIAL = 'TER', 'Земная группа'
        GAS_GIANT = 'GAS', 'Газовый гигант'
        ICE_GIANT = 'ICE', 'Ледяной гигант'
        DWARF = 'DWA', 'Карликовая планета'

    name = models.TextField(max_length=20, verbose_name="Название планеты")
    order = models.IntegerField(verbose_name="Порядок от солнца")
    planet_type = models.CharField(
        max_length=3,
        choices=PlanetType.choices,
        default=PlanetType.TERRESTRIAL,
        verbose_name="Тип планеты"
    )
    radius = models.FloatField(verbose_name="Радиус (км)")
    text = models.TextField(blank=True, null=True, verbose_name="Текст планеты")
    image = models.ImageField(upload_to='planets/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.name

class Satellite(models.Model):
    class SatelliteType(models.TextChoices):
        REGULAR = 'REG', 'Регулярный (сферический)'
        IRREGULAR = 'IRR', 'Нерегулярный (астероидный)'
        PROVISIONAL = 'PRO', 'Временный (захваченный)'
    name = models.TextField(max_length=20, verbose_name="Название спутника")
    planet = models.ForeignKey(
        'Planet', 
        on_delete=models.PROTECT, 
        related_name='satellites',
        verbose_name="Планета-хозяин"
    )
    satellite_type = models.CharField(
        max_length=3,
        choices=SatelliteType.choices,
        default=SatelliteType.REGULAR,
        verbose_name="Тип спутника"
    )
    radius = models.FloatField(verbose_name="Радиус (км)")
    text = models.TextField(blank=True, null=True, verbose_name="Текст спутника")
    image = models.ImageField(upload_to='satellites/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.name



class Mission(models.Model):
    class MissionType(models.TextChoices):
        MARS_ROVER = 'MRV', 'Марсоход'
        TELESCOPE = 'TEL', 'Телескоп'
        SPACESTATION = 'STA', 'Космическая станция'
        RESUPPLY = 'ORB', 'Орбитальный аппарат'
        OTHER = 'OTH', 'Другая'

    name = models.CharField(max_length=50, verbose_name="Название миссии")
    space_agency = models.ManyToManyField('SpaceAgency', related_name='missions', verbose_name='Космические агентства')
    mission_type = models.CharField(
        max_length=3,
        choices=MissionType.choices,
        default=MissionType.OTHER,
        verbose_name="Тип миссии"
    )
    launch_date = models.DateField(verbose_name="Дата запуска")
    # массивы с планетами и спутниками которые являются целями
    target_planets = models.ManyToManyField('Planet', blank=True, verbose_name="Цели (планеты)")
    target_satellites = models.ManyToManyField('Satellite', blank=True, verbose_name="Цели (спутники)")

    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        COMPLETED = 'completed', 'Завершена'
        PLANNED = 'planned', 'Планируется'

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNED,
        verbose_name='Статус'
    )

    def save(self, *args, **kwargs):
        # автоматический расчет
        if self.status == self.StatusChoices.ACTIVE and self.launch_date:
            delta = timezone.now().date() - self.launch_date
            self.duration_days = delta.days
        super().save(*args, **kwargs)

    duration_days = models.PositiveIntegerField(blank=True, null=True, verbose_name="Длительность (дней)")
    text = models.TextField(blank=True, null=True, verbose_name="Описание миссии")
    success = models.BooleanField(default=False, verbose_name="Успешность")
    image = models.ImageField(upload_to='missions/', blank=True, null=True, verbose_name='Изображение миссии')

    def display_space_agencies(self):
        return ", ".join([str(sa) for sa in self.space_agency.all()])
    display_space_agencies.short_description = "Агентства"

    def __str__(self):
        return self.name


class SpaceAgency(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название агентства")
    country = models.CharField(max_length=50, verbose_name="Страна")
    established_date = models.DateField(verbose_name="Дата основания")
    text = models.TextField(blank=True, null=True, verbose_name="Описание агентства")
    image = models.ImageField(upload_to='space_agencies/', blank=True, null=True, verbose_name='Изображение агентства')

    def __str__(self):
        return self.name

