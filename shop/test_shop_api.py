import pytest
from django.test import Client

from shop.models import Category, Product


@pytest.mark.django_db
def test_shop_api_invalid_page_returns_first_page():
    category = Category.objects.create(name='Книги', slug='books')
    Product.objects.create(
        category=category,
        name='Космическая книга',
        slug='space-book',
        description='Описание',
        price='100.00',
        stock=5,
    )

    response = Client().get('/shop/api/', {'page': 'abc'})

    assert response.status_code == 200
    assert response.json()['current_page'] == 1


@pytest.mark.django_db
def test_shop_api_returns_first_line_of_description():
    category = Category.objects.create(name='Книги', slug='books')
    Product.objects.create(
        category=category,
        name='Космическая книга',
        slug='space-book',
        description='Первая строка описания.\nВторая строка описания.',
        price='100.00',
        stock=5,
    )

    response = Client().get('/shop/api/')

    item = response.json()['results'][0]
    assert item['first_line'] == 'Первая строка описания.'
    assert item['description'] == 'Первая строка описания.\nВторая строка описания.'
