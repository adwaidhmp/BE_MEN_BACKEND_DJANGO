from .models import Order
from .serializer import UserOrderSerializer
from product.models import Product
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Order
from .serializer import CheckoutOrderSerializer

class UserOrdersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id=None):
        # If order_id is provided, return single order
        if order_id:
            try:
                order = Order.objects.select_related('product').get(id=order_id, user=request.user)
                serializer = UserOrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Otherwise, return all orders for the user
        orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')
        serializer = UserOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, order_id=None):
        if not order_id:
            return Response({'error': 'Order ID is required for delete'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status in ['SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED']:
            return Response({'error': 'Order cannot be cancelled at this stage'}, status=status.HTTP_400_BAD_REQUEST)

        order.order_status = 'CANCELLED'
        if order.payment_status == 'PAID':
            order.payment_status = 'REFUNDED'
            # Optional: trigger Razorpay refund here
        order.save()

        return Response({'message': 'Order cancelled successfully'}, status=status.HTTP_200_OK)
    





razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class CheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        orders_data = request.data.get('orders', [])

        if not orders_data:
            return Response({'error': 'No orders provided'}, status=400)

        # Validate payment method and check stock
        for order_data in orders_data:
            pm = order_data.get('payment_method')
            if pm not in ['COD', 'RAZORPAY']:
                return Response(
                    {'error': f'Invalid payment method for product {order_data.get("product")}'},
                    status=400
                )

            product = Product.objects.get(id=order_data['product'])
            if product.product_stock < order_data['quantity']:
                return Response(
                    {'error': f'Not enough stock for {product.name}'},
                    status=400
                )

        # Serialize and save orders
        serializer = CheckoutOrderSerializer(
            data=orders_data,
            many=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        orders = serializer.save()

        # For COD, reduce stock immediately
        if orders_data[0]['payment_method'] == 'COD':
            for order in orders:
                product = order.product
                product.product_stock -= order.quantity
                product.save()

        # Calculate total_amount
        total_amount = sum(order.total_amount for order in orders)

        # Response
        if orders_data[0]['payment_method'] == 'COD':
            return Response({
                'message': 'Orders placed successfully (COD)',
                'total_amount': total_amount,
                'orders': CheckoutOrderSerializer(orders, many=True).data
            }, status=201)
        else:
            # Razorpay
            amount_paise = int(total_amount * 100)
            razorpay_order = razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1
            })

            # Attach Razorpay order ID to all orders
            for order in orders:
                order.razorpay_order_id = razorpay_order['id']
                order.save()

            return Response({
                'message': 'Razorpay order created',
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': amount_paise,
                'currency': 'INR',
                'orders': CheckoutOrderSerializer(orders, many=True).data
            }, status=201)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from django.conf import settings
import razorpay

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class RazorpayVerifyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')

        # Verify signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
        except razorpay.errors.SignatureVerificationError:
            # Payment failed → delete orders
            orders = Order.objects.filter(razorpay_order_id=order_id)
            deleted_count, _ = orders.delete()
            return Response({'error': f'Payment verification failed, {deleted_count} order(s) deleted'}, status=400)

        # Payment verified → mark as PAID & reduce stock
        orders = Order.objects.filter(razorpay_order_id=order_id)
        for order in orders:
            order.payment_status = 'PAID'
            order.razorpay_payment_id = payment_id
            order.save()

            # Reduce stock
            product = order.product
            product.product_stock -= order.quantity
            product.save()

        return Response({'message': 'Payment successful', 'orders': [o.id for o in orders]}, status=200)