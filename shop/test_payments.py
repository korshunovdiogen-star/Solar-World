import json
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from shop import payments
from shop.models import CartItem, Category, Order, OrderItem, Product

User = get_user_model()


@pytest.fixture
def product():
    category = Category.objects.create(name="Книги", slug="books")
    return Product.objects.create(
        category=category,
        name="Космическая книга",
        slug="space-book",
        description="Описание",
        price=Decimal("100.00"),
        stock=5,
    )


@pytest.fixture
def checkout_data():
    return {
        "first_name": "Иван",
        "last_name": "Космонавтов",
        "email": "ivan@example.com",
        "phone": "+7 900 000-00-00",
        "address": "г. Москва, ул. Гагарина, д. 1",
    }


def configure_provider(monkeypatch):
    monkeypatch.setattr(settings, "YOOKASSA_SHOP_ID", "test-shop")
    monkeypatch.setattr(settings, "YOOKASSA_SECRET_KEY", "test-secret")


def fake_payment(order, **overrides):
    payment = {
        "id": order.payment_id,
        "status": "succeeded",
        "paid": True,
        "amount": {"value": f"{order.total:.2f}", "currency": "RUB"},
        "metadata": {"order_id": str(order.pk)},
    }
    payment.update(overrides)
    return payment


def create_order_with_item(product, session_key="test-session", payment_id="pay-1"):
    order = Order.objects.create(
        session_key=session_key,
        first_name="Иван",
        last_name="Космонавтов",
        email="ivan@example.com",
        phone="+7 900 000-00-00",
        address="г. Москва",
        total=Decimal("200.00"),
        payment_id=payment_id,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price,
    )
    return order


@pytest.mark.django_db
def test_checkout_creates_order_and_redirects_to_provider(product, checkout_data, monkeypatch):
    configure_provider(monkeypatch)
    captured = {}

    def fake_create_payment(order, return_url):
        captured["order"] = order
        captured["return_url"] = return_url
        return {
            "id": "pay-1",
            "confirmation": {"confirmation_url": "https://yookassa.test/checkout"},
        }

    monkeypatch.setattr(payments, "create_payment", fake_create_payment)

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})

    response = client.post(reverse("shop:checkout"), checkout_data)

    order = Order.objects.get()
    assert response.status_code == 302
    assert response.url == "https://yookassa.test/checkout"
    assert order.total == Decimal("200.00")
    assert order.status == "pending"
    assert order.payment_id == "pay-1"
    assert order.session_key == client.session.session_key

    item = order.items.get()
    assert item.product == product
    assert item.quantity == 2
    assert item.price == product.price

    assert captured["order"] == order
    assert f"order={order.pk}" in captured["return_url"]
    assert CartItem.objects.filter(product=product).exists()


@pytest.mark.django_db
def test_checkout_saves_customer_details(product, checkout_data, monkeypatch):
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        payments,
        "create_payment",
        lambda order, return_url: {
            "id": "pay-1",
            "confirmation": {"confirmation_url": "https://yookassa.test/checkout"},
        },
    )

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 1})
    client.post(reverse("shop:checkout"), checkout_data)

    order = Order.objects.get()
    assert order.first_name == "Иван"
    assert order.email == "ivan@example.com"
    assert order.phone == "+7 900 000-00-00"
    assert order.address == "г. Москва, ул. Гагарина, д. 1"


@pytest.mark.django_db
def test_checkout_rejects_quantity_over_stock(product, checkout_data, monkeypatch):
    configure_provider(monkeypatch)

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})
    product.stock = 1
    product.save(update_fields=["stock"])

    response = client.post(reverse("shop:checkout"), checkout_data)

    assert response.status_code == 200
    assert "осталось только 1" in response.content.decode()
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_checkout_handles_provider_error(product, checkout_data, monkeypatch):
    configure_provider(monkeypatch)

    def failing_create_payment(order, return_url):
        raise payments.PaymentError("provider is down")

    monkeypatch.setattr(payments, "create_payment", failing_create_payment)

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 1})

    response = client.post(reverse("shop:checkout"), checkout_data)

    order = Order.objects.get()
    assert response.status_code == 200
    assert "Не удалось перейти к оплате" in response.content.decode()
    assert order.status == "cancelled"


@pytest.mark.django_db
def test_checkout_requires_provider_configuration(product, checkout_data, monkeypatch):
    monkeypatch.setattr(settings, "YOOKASSA_SHOP_ID", "")
    monkeypatch.setattr(settings, "YOOKASSA_SECRET_KEY", "")

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 1})

    response = client.post(reverse("shop:checkout"), checkout_data)

    assert response.status_code == 200
    assert "платёжный сервис не настроен" in response.content.decode()
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_payment_return_marks_order_paid_and_clears_cart(product, checkout_data, monkeypatch):
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        payments,
        "create_payment",
        lambda order, return_url: {
            "id": "pay-1",
            "confirmation": {"confirmation_url": "https://yookassa.test/checkout"},
        },
    )

    client = Client()
    client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": 2})
    client.post(reverse("shop:checkout"), checkout_data)

    order = Order.objects.get()
    monkeypatch.setattr(payments, "fetch_payment", lambda payment_id: fake_payment(order))

    response = client.get(reverse("shop:payment_return"), {"order": order.pk})

    order.refresh_from_db()
    product.refresh_from_db()

    assert response.status_code == 200
    assert "оплачен" in response.content.decode()
    assert order.status == "paid"
    assert not CartItem.objects.filter(product=product).exists()
    assert product.stock == 3


@pytest.mark.django_db
def test_payment_return_is_idempotent(product, monkeypatch):
    order = create_order_with_item(product)
    monkeypatch.setattr(payments, "fetch_payment", lambda payment_id: fake_payment(order))

    client = Client()
    session = client.session
    session["marker"] = True
    session.save()
    order.session_key = session.session_key
    order.save(update_fields=["session_key"])

    first = client.get(reverse("shop:payment_return"), {"order": order.pk})
    second = client.get(reverse("shop:payment_return"), {"order": order.pk})

    order.refresh_from_db()
    product.refresh_from_db()

    assert first.status_code == 200
    assert second.status_code == 200
    assert order.status == "paid"
    assert product.stock == 3


@pytest.mark.django_db
def test_payment_return_hides_another_users_order(product):
    order = create_order_with_item(product, session_key="someone-else")

    response = Client().get(reverse("shop:payment_return"), {"order": order.pk})

    assert response.status_code == 404


@pytest.mark.django_db
def test_payment_return_marks_cancelled_payment(product, monkeypatch):
    order = create_order_with_item(product)
    monkeypatch.setattr(
        payments,
        "fetch_payment",
        lambda payment_id: fake_payment(order, status="canceled", paid=False),
    )

    client = Client()
    session = client.session
    session["marker"] = True
    session.save()
    order.session_key = session.session_key
    order.save(update_fields=["session_key"])

    response = client.get(reverse("shop:payment_return"), {"order": order.pk})

    order.refresh_from_db()

    assert response.status_code == 200
    assert "Платёж отменён" in response.content.decode()
    assert order.status == "cancelled"


@pytest.mark.django_db
def test_webhook_marks_order_paid(product, monkeypatch):
    configure_provider(monkeypatch)
    order = create_order_with_item(product)
    monkeypatch.setattr(payments, "fetch_payment", lambda payment_id: fake_payment(order))

    response = Client().post(
        reverse("shop:payment_webhook"),
        data=json.dumps(
            {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {"id": order.payment_id, "status": "succeeded"},
            }
        ),
        content_type="application/json",
    )

    order.refresh_from_db()

    assert response.status_code == 200
    assert order.status == "paid"


@pytest.mark.django_db
def test_webhook_does_not_trust_request_body(product, monkeypatch):
    configure_provider(monkeypatch)
    order = create_order_with_item(product)
    monkeypatch.setattr(
        payments,
        "fetch_payment",
        lambda payment_id: fake_payment(order, amount={"value": "1.00", "currency": "RUB"}),
    )

    response = Client().post(
        reverse("shop:payment_webhook"),
        data=json.dumps(
            {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {"id": order.payment_id, "status": "succeeded"},
            }
        ),
        content_type="application/json",
    )

    order.refresh_from_db()

    assert response.status_code == 200
    assert order.status == "pending"


@pytest.mark.django_db
def test_webhook_ignores_unknown_payment():
    response = Client().post(
        reverse("shop:payment_webhook"),
        data=json.dumps(
            {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {"id": "unknown-payment"},
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_webhook_requires_post():
    response = Client().get(reverse("shop:payment_webhook"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_webhook_rejects_invalid_json():
    response = Client().post(
        reverse("shop:payment_webhook"),
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400
