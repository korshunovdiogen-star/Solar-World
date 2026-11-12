from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.shop_page, name="shop_catalog"),
    path("api/", views.shop_api, name="shop_api"),
    path("shop/api/categories/", views.category_options, name="category-options"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/set/<int:pk>/", views.cart_set_quantity, name="cart_set_quantity"),
    path("cart/update/<int:item_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("cart/checkout/", views.checkout, name="checkout"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("payment/webhook/", views.payment_webhook, name="payment_webhook"),
]
