from rest_framework import serializers
from order.models import Order

class AdminOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        # Admin can update order status, tracking id, and delivery date
        fields = [
            "id",
            "order_status",
            "tracking_id",
            "delivery_date",
        ]
