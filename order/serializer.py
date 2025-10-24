from product.models import Product
from product.serializer import ProductSerializer
from rest_framework import serializers

from .models import Notification, Order


class UserOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "product",
            "quantity",
            "price",
            "total_amount",
            "payment_status",
            "payment_method",
            "order_status",
            "tracking_id",
            "delivery_date",
            "shipping_address",
            "phone",
            "created_at",
        ]
        read_only_fields = [
            "payment_status",
            "tracking_id",
            "delivery_date",
            "price",
            "total_amount" "created_at",
            "order_status",
            "payment_method",
        ]


class CheckoutOrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Order
        fields = [
            "product",
            "quantity",
            "shipping_address",
            "phone",
            "total_amount",
            "payment_method",
        ]
        read_only_fields = ["total_amount", "price"]

    def create(self, validated_data):
        product = validated_data["product"]
        quantity = validated_data.get("quantity", 1)

        # Assign unit price from product
        price = product.price
        total_amount = price * quantity

        order = Order.objects.create(
            user=self.context["request"].user,
            product=product,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            shipping_address=validated_data.get("shipping_address", ""),
            phone=validated_data.get("phone", ""),
            payment_method=validated_data.get("payment_method", "COD"),
        )
        return order


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "created_at", "read"]
        read_only_fields = ["id", "message", "created_at"]


class OrderReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['return_reason']

    def validate(self, data):
        order = self.instance
        if order.order_status != "DELIVERED":
            raise serializers.ValidationError("Only delivered orders can be returned.")
        if not data.get("return_reason"):
            raise serializers.ValidationError("Return reason is required.")
        return data 