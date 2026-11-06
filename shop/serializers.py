from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    image_url = serializers.SerializerMethodField()
    first_line = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "first_line",
            "price",
            "image",
            "image_url",
            "stock",
            "available",
            "category",
            "category_name",
            "category_slug",
            "created",
            "updated",
        )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_first_line(self, obj):
        """Первая строка описания товара для карточки."""
        if not obj.description:
            return ""
        lines = obj.description.splitlines()
        return lines[0] if lines else ""
