import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from planets.models import Planet
from shop.models import Cart, CartItem, Category, Product
from users.models import Favorite

User = get_user_model()


@pytest.fixture
def category():
    return Category.objects.create(name="Книги", slug="books")


@pytest.fixture
def planet():
    return Planet.objects.create(
        name="Марс",
        order=4,
        radius=3390,
        planet_type="TER",
        text="Первая строка.",
    )


@pytest.fixture
def product(category):
    return Product.objects.create(
        category=category,
        name="Космическая книга",
        slug="space-book",
        description="Первая строка.\nВторая строка.",
        price=Decimal("100.00"),
        stock=5,
    )


@pytest.mark.django_db
def test_shop_api_returns_all_products(category):
    for index in range(15):
        Product.objects.create(
            category=category,
            name=f"Товар {index}",
            slug=f"product-{index}",
            description="Описание",
            price="10.00",
            stock=1,
        )

    response = Client().get(reverse("shop:shop_api"))

    data = response.json()
    assert len(data["results"]) == 15
    assert data["total_pages"] == 1
    assert data["current_page"] == 1


@pytest.mark.django_db
def test_shop_api_includes_detail_url(product):
    response = Client().get(reverse("shop:shop_api"))

    item = response.json()["results"][0]
    assert item["detail_url"] == reverse("shop:product_detail", args=[product.pk])


@pytest.mark.django_db
def test_product_detail_page_shows_product(product):
    response = Client().get(reverse("shop:product_detail", args=[product.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert product.name in content
    assert "Добавить в корзину" in content
    assert reverse("shop:cart_add", args=[product.pk]) in content


@pytest.mark.django_db
def test_product_detail_page_hides_unavailable_product(product):
    product.available = False
    product.save(update_fields=["available"])

    response = Client().get(reverse("shop:product_detail", args=[product.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_anonymous_cart_add_and_total(product):
    client = Client()

    response = client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})

    assert response.status_code == 302
    cart = Cart.objects.get(session_key=client.session.session_key)
    item = cart.items.get(product=product)
    assert item.quantity == 2
    assert cart.get_total() == product.price * 2


@pytest.mark.django_db
def test_cart_add_increments_existing_item(product):
    client = Client()

    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 1})

    item = CartItem.objects.get(product=product)
    assert item.quantity == 3


@pytest.mark.django_db
def test_cart_add_is_limited_by_stock(product):
    client = Client()

    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 99})

    item = CartItem.objects.get(product=product)
    assert item.quantity == product.stock


@pytest.mark.django_db
def test_cart_update_and_remove(product):
    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})
    item = CartItem.objects.get(product=product)

    client.post(reverse("shop:cart_update", args=[item.pk]), {"quantity": 4})
    item.refresh_from_db()
    assert item.quantity == 4

    client.post(reverse("shop:cart_remove", args=[item.pk]))
    assert not CartItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_user_cannot_change_another_user_cart(product):
    first = User.objects.create_user(username="first", password="pass")
    second = User.objects.create_user(username="second", password="pass")

    first_cart = Cart.objects.create(user=first)
    item = CartItem.objects.create(cart=first_cart, product=product, quantity=1)

    client = Client()
    client.force_login(second)

    assert (
        client.post(reverse("shop:cart_update", args=[item.pk]), {"quantity": 2}).status_code == 404
    )
    assert client.post(reverse("shop:cart_remove", args=[item.pk])).status_code == 404

    item.refresh_from_db()
    assert item.quantity == 1


@pytest.mark.django_db
def test_cart_checkout_shows_stub(product):
    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})

    response = client.post(reverse("shop:checkout"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Оплата пока недоступна" in content
    assert "200" in content


@pytest.mark.django_db
def test_product_can_be_added_to_favorites(product, client):
    user = User.objects.create_user(username="fav-user", password="pass")
    client.force_login(user)

    response = client.post(
        reverse("toggle_favorite"),
        json.dumps({"content_type": "product", "object_id": product.pk}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is True
    content_type = ContentType.objects.get_for_model(Product)
    assert Favorite.objects.filter(
        user=user, content_type=content_type, object_id=product.pk
    ).exists()


@pytest.mark.django_db
def test_profile_splits_article_and_product_favorites(product, planet, client):
    user = User.objects.create_user(username="profile-user", password="pass")
    product_type = ContentType.objects.get_for_model(Product)
    planet_type = ContentType.objects.get_for_model(planet)
    Favorite.objects.create(user=user, content_type=product_type, object_id=product.pk)
    Favorite.objects.create(user=user, content_type=planet_type, object_id=planet.pk)

    client.force_login(user)
    response = client.get(reverse("profile"))

    assert response.status_code == 200
    assert list(response.context["article_favorites"])[0].content_object == planet
    assert list(response.context["product_favorites"])[0].content_object == product
