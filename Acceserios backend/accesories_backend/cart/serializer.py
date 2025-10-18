from rest_framework import serializers
from cart.models import Cart
from product.serializer import ProductSerializer


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity']