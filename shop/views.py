import json
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from users.models import Favorite

from .models import Cart, CartItem, Category, Product
from .serializers import ProductSerializer

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

    queryset = Product.objects.filter(available=True)

    if q:
        queryset = queryset.filter(name__icontains=q)

    if category_slug != "all":
        try:
            category = Category.objects.get(slug=category_slug)
            queryset = queryset.filter(category=category)
        except Category.DoesNotExist:
            return JsonResponse(
                {
                    "results": [],
                    "total_pages": 1,
                    "current_page": 1,
                }
            )

    sort_field = SORT_MAP.get(ordering, "name")
    queryset = queryset.order_by(sort_field)

    serializer = ProductSerializer(queryset, many=True, context={"request": request})

    return JsonResponse(
        {
            "results": serializer.data,
            "total_pages": 1,
            "current_page": 1,
        }
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

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "is_favorite": is_favorite,
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


def _parse_quantity(raw, default=None):
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return default
    if quantity < 1 or quantity > MAX_QUANTITY:
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


@require_POST
def cart_checkout(request):
    cart = _get_cart(request)
    items = list(cart.items.select_related("product")) if cart else []

    return render(
        request,
        "shop/checkout_stub.html",
        {
            "items": items,
            "total": _cart_total(items),
        },
    )
