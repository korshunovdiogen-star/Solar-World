from django.contrib import admin

from .models import Cart, CartItem, Category, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "stock", "available", "created")
    list_filter = ("category", "available", "created")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "stock", "available")
    ordering = ("-created",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created", "get_total")
    list_filter = ("created",)
    search_fields = ("user__username", "session_key")
    readonly_fields = ("created",)

    def get_total(self, obj):
        return obj.get_total()

    get_total.short_description = "Итого"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "total_price")
    search_fields = ("product__name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "first_name", "last_name", "email", "total", "status", "created")
    list_filter = ("status", "created", "updated")
    search_fields = ("user__username", "first_name", "last_name", "email", "phone")
    list_editable = ("status",)
    readonly_fields = ("created", "updated")
    fieldsets = (
        (
            "Покупатель",
            {
                "fields": (
                    "user",
                    "session_key",
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "address",
                )
            },
        ),
        ("Оплата", {"fields": ("total", "status", "payment_id")}),
        ("Даты", {"fields": ("created", "updated")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price")
    search_fields = ("product__name",)
