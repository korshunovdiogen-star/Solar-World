from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.shop_page, name="shop_catalog"),
    path("api/", views.shop_api, name="shop_api"),
    path("shop/api/categories/", views.category_options, name="category-options"),
]
