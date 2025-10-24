from rest_framework import serializers

from .models import Product, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "category"]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    product_image = serializers.ImageField(use_url=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "description",
            "price",
            "old_price",
            "product_stock",
            "active",
            "product_image",
            "created_at",
            "updated_at",
        ]
