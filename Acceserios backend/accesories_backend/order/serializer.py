from rest_framework import serializers
from product.serializer import ProductSerializer
from product.models import Product
from .models import Order


class UserOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'product',
            'quantity',
            'price',
            'total_amount',
            'payment_status',
            'order_status',
            'tracking_id',
            'delivery_date',
            'shipping_address',
            'phone',
            'created_at'
        ]
        read_only_fields = [
            'payment_status',
            'tracking_id',
            'delivery_date',
            'price',
            'total_amount'
            'created_at',
            'order_status'
        ]
        
        

#user buying serializer
class CheckoutOrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Order
        fields = [
            'product',
            'quantity',
            'shipping_address',
            'phone',
            'total_amount',
            'payment_method',
        ]
        read_only_fields = [ 'total_amount','price']

    def create(self, validated_data):
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)
        
        # Assign unit price from product
        price = product.price  
        total_amount = price * quantity

        order = Order.objects.create(
            user=self.context['request'].user,
            product=product,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            shipping_address=validated_data.get('shipping_address', ''),
            phone=validated_data.get('phone', ''),
            payment_method=validated_data.get('payment_method', 'COD')
        )
        return order