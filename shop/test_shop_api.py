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
