import logging
import uuid
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Ошибка обращения к платёжному провайдеру."""


def is_configured():
    return bool(settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY)


def _request(method, path, **kwargs):
    if not is_configured():
        raise PaymentError("Платёжный провайдер не настроен")

    url = f"{settings.YOOKASSA_API_URL.rstrip('/')}{path}"

    try:
        response = requests.request(
            method,
            url,
            auth=(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY),
            timeout=settings.PAYMENT_REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as exc:
        logger.exception("Платёжный сервис недоступен")
        raise PaymentError("Платёжный сервис недоступен") from exc

    if not response.ok:
        logger.warning(
            "Платёжный сервис ответил %s на %s: %s",
            response.status_code,
            path,
            response.text[:300],
        )
        raise PaymentError(f"Платёжный сервис вернул ошибку {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        raise PaymentError("Платёжный сервис вернул некорректный ответ") from exc


def create_payment(order, return_url):
    data = _request(
        "POST",
        "/payments",
        headers={"Idempotence-Key": str(uuid.uuid4())},
        json={
            "amount": {
                "value": f"{order.total:.2f}",
                "currency": "RUB",
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
            "description": f"Оплата заказа №{order.pk}",
            "metadata": {"order_id": str(order.pk)},
        },
    )

    confirmation = data.get("confirmation") or {}
    if not data.get("id") or not confirmation.get("confirmation_url"):
        raise PaymentError("Платёжный сервис не вернул ссылку на оплату")

    return data


def fetch_payment(payment_id):
    return _request("GET", f"/payments/{quote(str(payment_id), safe='')}")
