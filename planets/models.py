from django.db import models

class Planet(models.Model):
    class PlanetType(models.TextChoices):
        TERRESTRIAL = 'TER', 'Земная группа'
        GAS_GIANT = 'GAS', 'Газовый гигант'
        ICE_GIANT = 'ICE', 'Ледяной гигант'
        DWARF = 'DWA', 'Карликовая планета'

    planet_name = models.TextField(max_length=20, verbose_name="Название планеты")
    planet_orger = models.IntegerField(verbose_name="Порядок от солнца")
    planet_type = models.CharField(
        max_length=3,
        choices=PlanetType.choices,
        default=PlanetType.TERRESTRIAL,
        verbose_name="Тип планеты"
    )
    planet_radius = models.FloatField(verbose_name="Радиус (км)")
    planet_text = models.TextField(verbose_name="Текст планеты")
    image = models.ImageField(upload_to='planets/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.planet_name

class Satellite(models.Model):
    class SatelliteType(models.TextChoices):
        REGULAR = 'REG', 'Регулярный (сферический)'
        IRREGULAR = 'IRR', 'Нерегулярный (астероидный)'
        PROVISIONAL = 'PRO', 'Временный (захваченный)'
        ARTIFICIAL = 'ART', 'Искусственный (станции\зонды)'
    satellite_name = models.TextField(max_length=20, verbose_name="Название спутника")
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
    satellite_radius = models.FloatField(verbose_name="Радиус (км)")
    satellite_text = models.TextField(verbose_name="Текст спутника")
    image = models.ImageField(upload_to='satellites/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.satellite_name

