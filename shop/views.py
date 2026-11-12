import json
import logging
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F, Q, Value
from django.db.models.functions import Greatest
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from solarWorld.utils import paginated_json_response, parse_page_number, search_and_sort
from users.models import Favorite

from . import payments
from .forms import CheckoutForm
from .models import Cart, CartItem, Category, Order, OrderItem, Product
from .serializers import ProductSerializer

logger = logging.getLogger(__name__)

MAX_QUANTITY = 99


def shop_page(request):
    categories = dict(Category.objects.order_by("name").values_list("slug", "name"))
    return render(
        request,
        "shop/shop_catalog.html",
        {
            "category_options_json": json.dumps(categories, ensure_ascii=False),
        },
    )


SORT_MAP = {
    "name_asc": "name",
    "name_desc": "-name",
    "price_asc": "price",
    "price_desc": "-price",
    "stock_asc": "stock",
    "stock_desc": "-stock",
    "category_asc": "category__name",
    "category_desc": "-category__name",
}


@cache_page(60 * 15)
def shop_api(request):
    q = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "all")
    ordering = request.GET.get("ordering", "name_asc")
    page = parse_page_number(request.GET.get("page", 1))

    queryset = Product.objects.filter(available=True)

    if category_slug != "all":
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(category=category)

    queryset = search_and_sort(queryset, q, SORT_MAP, ordering)

    return paginated_json_response(
        queryset,
        page,
        lambda products: ProductSerializer(products, many=True, context={"request": request}).data,
    )


@cache_page(60 * 60)
def category_options(request):

    options = dict(Category.objects.order_by("name").values_list("slug", "name"))
    return JsonResponse(options)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)

    is_favorite = False
    if request.user.is_authenticated:
        content_type = ContentType.objects.get_for_model(Product)
        is_favorite = Favorite.objects.filter(
            user=request.user, content_type=content_type, object_id=product.pk
        ).exists()

    cart = _get_cart(request)
    cart_item = cart.items.filter(product=product).first() if cart else None

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "is_favorite": is_favorite,
            "cart_item": cart_item,
        },
    )


def _get_cart(request, create=False):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).order_by("id").first()
        if cart is None and create:
            cart = Cart.objects.create(user=request.user)
        return cart

    session_key = request.session.session_key
    if not session_key:
        if not create:
            return None
        request.session.create()
        session_key = request.session.session_key

    cart = Cart.objects.filter(session_key=session_key, user__isnull=True).order_by("id").first()
    if cart is None and create:
        cart = Cart.objects.create(session_key=session_key)
    return cart


def _parse_quantity(raw, default=None, allow_zero=False):
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return default
    minimum = 0 if allow_zero else 1
    if quantity < minimum or quantity > MAX_QUANTITY:
        return default
    return quantity


def _cart_total(items):
    return sum((item.product.price * item.quantity for item in items), Decimal("0"))


def cart_detail(request):
    cart = _get_cart(request)
    items = list(cart.items.select_related("product")) if cart else []

    return render(
        request,
        "shop/cart.html",
        {
            "items": items,
            "total": _cart_total(items),
        },
    )


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    quantity = _parse_quantity(request.POST.get("quantity"), default=1)

    if product.stock < 1:
        return redirect("shop:cart")

    cart = _get_cart(request, create=True)
    item, _ = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": 0},
    )
    item.quantity = min(item.quantity + quantity, product.stock, MAX_QUANTITY)
    item.save(update_fields=["quantity"])

    return redirect("shop:cart")


@require_POST
def cart_set_quantity(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    quantity = _parse_quantity(request.POST.get("quantity"), allow_zero=True)

    if quantity is None:
        return JsonResponse({"error": "Некорректное количество"}, status=400)

    cart = _get_cart(request, create=quantity > 0 and product.stock > 0)
    item = cart.items.filter(product=product).first() if cart else None

    if quantity == 0 or product.stock < 1:
        if item is not None:
            item.delete()
            item = None
        quantity = 0
    else:
        quantity = min(quantity, product.stock, MAX_QUANTITY)
        if item is None:
            item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        else:
            item.quantity = quantity
            item.save(update_fields=["quantity"])

    items = list(cart.items.select_related("product")) if cart else []

    return JsonResponse(
        {
            "quantity": quantity if item is not None else 0,
            "item_id": item.pk if item is not None else None,
            "in_cart": item is not None,
            "total": str(_cart_total(items)),
            "total_items": sum(cart_item.quantity for cart_item in items),
        }
    )


@require_POST
def cart_update(request, item_id):
    cart = _get_cart(request)
    item = get_object_or_404(
        CartItem.objects.select_related("product"),
        pk=item_id,
        cart=cart,
    )
    quantity = _parse_quantity(request.POST.get("quantity"))

    if quantity is None:
        return redirect("shop:cart")

    quantity = min(quantity, item.product.stock)
    if quantity < 1:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])

    return redirect("shop:cart")


@require_POST
def cart_remove(request, item_id):
    cart = _get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    return redirect("shop:cart")


def _checkout_initial(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }


def _cart_problems(items):
    problems = []

    for item in items:
        if not item.product.available:
            problems.append(f"Товар «{item.product.name}» больше не продаётся.")
        elif item.product.stock < 1:
            problems.append(f"Товара «{item.product.name}» нет в наличии.")
        elif item.quantity > item.product.stock:
            problems.append(
                f"Товара «{item.product.name}» осталось только {item.product.stock} шт."
            )

    return problems


@transaction.atomic
def _create_order(request, items, data):
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=None if request.user.is_authenticated else request.session.session_key,
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone=data["phone"],
        address=data["address"],
        total=_cart_total(items),
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            for item in items
        ]
    )

    return order


def _payment_return_url(request, order):
    base = settings.PAYMENT_RETURN_URL or request.build_absolute_uri(reverse("shop:payment_return"))
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{urlencode({'order': order.pk})}"


def _cart_for_order(order):
    if order.user_id:
        return Cart.objects.filter(user_id=order.user_id).order_by("id").first()

    if order.session_key:
        return (
            Cart.objects.filter(session_key=order.session_key, user__isnull=True)
            .order_by("id")
            .first()
        )

    return None


@transaction.atomic
def _mark_order_paid(order):
    locked = Order.objects.select_for_update().get(pk=order.pk)

    if locked.status == "paid":
        return False

    locked.status = "paid"
    locked.save(update_fields=["status", "updated"])

    cart = _cart_for_order(locked)
    if cart is not None:
        cart.items.all().delete()

    for item in locked.items.all():
        Product.objects.filter(pk=item.product_id).update(
            stock=Greatest(F("stock") - item.quantity, Value(0))
        )

    order.status = "paid"
    return True


def _apply_payment_status(order, payment):
    if str(payment.get("id", "")) != str(order.payment_id or ""):
        return False

    metadata = payment.get("metadata") or {}
    if str(metadata.get("order_id", "")) != str(order.pk):
        logger.warning("Платёж %s не относится к заказу %s", order.payment_id, order.pk)
        return False

    amount = payment.get("amount") or {}
    if amount.get("currency") != "RUB" or str(amount.get("value")) != f"{order.total:.2f}":
        logger.warning("Сумма платежа %s не совпадает с заказом %s", order.payment_id, order.pk)
        return False

    status = payment.get("status")

    if status == "succeeded":
        return _mark_order_paid(order)

    if status == "canceled" and order.status == "pending":
        order.status = "cancelled"
        order.save(update_fields=["status", "updated"])

    return False


def _get_order_for_request(request, raw_order_id):
    try:
        order_id = int(raw_order_id)
    except (TypeError, ValueError):
        return None

    queryset = Order.objects.filter(pk=order_id)
    session_key = request.session.session_key

    if request.user.is_authenticated:
        ownership = Q(user=request.user)
        if session_key:
            ownership |= Q(user__isnull=True, session_key=session_key)
        return queryset.filter(ownership).first()

    if not session_key:
        return None

    return queryset.filter(user__isnull=True, session_key=session_key).first()


def checkout(request):
    cart = _get_cart(request)
    items = list(cart.items.select_related("product")) if cart else []

    if not items:
        return redirect("shop:cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            problems = _cart_problems(items)

            if problems:
                for problem in problems:
                    form.add_error(None, problem)
            elif not payments.is_configured():
                form.add_error(
                    None,
                    "Оплата временно недоступна: платёжный сервис не настроен.",
                )
            else:
                order = _create_order(request, items, form.cleaned_data)

                try:
                    payment = payments.create_payment(
                        order,
                        _payment_return_url(request, order),
                    )
                except payments.PaymentError:
                    logger.exception("Не удалось создать платёж для заказа %s", order.pk)
                    order.status = "cancelled"
                    order.save(update_fields=["status", "updated"])
                    form.add_error(None, "Не удалось перейти к оплате. Попробуйте ещё раз.")
                else:
                    order.payment_id = payment["id"]
                    order.save(update_fields=["payment_id", "updated"])
                    return redirect(payment["confirmation"]["confirmation_url"])
    else:
        form = CheckoutForm(initial=_checkout_initial(request))

    return render(
        request,
        "shop/checkout.html",
        {
            "form": form,
            "items": items,
            "total": _cart_total(items),
            "payments_configured": payments.is_configured(),
            "test_mode": settings.PAYMENT_TEST_MODE,
        },
    )


def payment_return(request):
    order = _get_order_for_request(request, request.GET.get("order"))

    if order is None:
        raise Http404

    state = "pending"

    if order.status == "paid":
        state = "paid"
    elif not order.payment_id:
        state = "error"
    else:
        try:
            payment = payments.fetch_payment(order.payment_id)
        except payments.PaymentError:
            logger.warning("Не удалось проверить платёж %s", order.payment_id)
            state = "error"
        else:
            _apply_payment_status(order, payment)
            order.refresh_from_db()

            if order.status == "paid":
                state = "paid"
            elif order.status == "cancelled":
                state = "cancelled"

    return render(
        request,
        "shop/payment_result.html",
        {
            "order": order,
            "state": state,
            "test_mode": settings.PAYMENT_TEST_MODE,
        },
    )


@csrf_exempt
@require_POST
def payment_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    if payload.get("event") not in {"payment.succeeded", "payment.canceled"}:
        return HttpResponse(status=200)

    payment_id = (payload.get("object") or {}).get("id")
    if not payment_id:
        return HttpResponse(status=200)

    order = Order.objects.filter(payment_id=payment_id).first()
    if order is None:
        return HttpResponse(status=200)

    if not payments.is_configured():
        logger.error("Вебхук ЮKassa получен, но платёжный сервис не настроен")
        return HttpResponse(status=503)

    try:
        payment = payments.fetch_payment(payment_id)
    except payments.PaymentError:
        logger.warning("Не удалось проверить платёж %s по вебхуку", payment_id)
        return HttpResponse(status=502)

    _apply_payment_status(order, payment)
    return HttpResponse(status=200)
