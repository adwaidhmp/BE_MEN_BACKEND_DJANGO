from Be_men_user.serializers import UserProfileSerializer
from order.models import Order
from product.serializer import ProductSerializer
from rest_framework import serializers


class AdminOrderSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_status",
            "tracking_id",
            "delivery_date",
            "payment_status",
            "payment_method",
            "shipping_address",
            "total_amount",
            "created_at",
            "quantity",
            "user",
            "product",
            "cancellation_reason",
            "cancelled_at",
        ]


class CancelledOrderSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "cancellation_reason",
            "cancelled_at",
            "user",
            "product",
            "total_amount",
            "quantity",
            'return_reason',
            'returned_at'
        ]
