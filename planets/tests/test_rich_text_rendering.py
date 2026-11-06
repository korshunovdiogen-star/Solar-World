import pytest
from django.test import Client
from django.urls import reverse

from planets.models import Planet


@pytest.mark.django_db
def test_detail_page_sanitizes_rich_text():
    planet = Planet.objects.create(
        name="Марс",
        order=4,
        radius=3390,
        planet_type="TER",
        text=(
            "Заголовок\n"
            '<span class="custom-style" onclick="alert(1)">Марс</span> '
            "<script>alert(1)</script>"
        ),
    )

    response = Client().get(reverse("planet_detail", args=[planet.id]))
    content = response.content.decode()

    assert response.status_code == 200
    assert '<span class="custom-style">Марс</span>' in content
    assert "onclick" not in content
    assert "<script>alert(1)</script>" not in content


@pytest.mark.django_db
def test_detail_page_survives_planet_without_text():
    planet = Planet.objects.create(
        name="Без текста",
        order=1,
        radius=1000,
        planet_type="TER",
        text=None,
    )

    response = Client().get(reverse("planet_detail", args=[planet.id]))

    assert response.status_code == 200
