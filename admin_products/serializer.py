from product.models import Product, ProductCategory
from rest_framework import serializers


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "category"]


class AdminProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "description",
            "price",
            "old_price",
            "product_image",
            "product_stock",
            "active",
            "created_at",
            "updated_at",
        ]
