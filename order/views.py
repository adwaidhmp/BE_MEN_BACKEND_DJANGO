import razorpay
from django.conf import settings
from django.utils import timezone
from product.models import Product
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, Order
from .serializer import (CheckoutOrderSerializer, NotificationSerializer,
                         UserOrderSerializer,OrderReturnSerializer)

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)
from cart.models import Cart
from django.db import transaction
from django.db.models import F
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class UserOrdersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id=None):
        # If order_id is provided, return single order
        if order_id:
            try:
                order = Order.objects.select_related("product").get(
                    id=order_id, user=request.user
                )
                serializer = UserOrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Otherwise, return all orders for the user
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("product")
            .order_by("-created_at")
        )
        serializer = UserOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, order_id=None):
        if not order_id:
            return Response(
                {"error": "Order ID is required for delete"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.select_related("product").get(
                id=order_id, user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if order.order_status in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]:
            return Response(
                {"error": "Order cannot be cancelled at this stage"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cancellation_reason = request.data.get("cancellation_reason", "")
        if not cancellation_reason:
            return Response(
                {"error": "Cancellation reason is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = order.product
        product.product_stock += order.quantity
        product.save()

        order.order_status = "CANCELLED"
        order.cancellation_reason = cancellation_reason
        order.cancelled_at = timezone.now()
        if order.payment_status == "PAID":
            order.payment_status = "REFUNDED"
            # Optional: trigger Razorpay refund here
        order.save()

        return Response(
            {"message": "Order cancelled successfully"}, status=status.HTTP_200_OK
        )

class ReturnRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderReturnSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            order.order_status = "RETURN_PENDING"
            order.save()
            return Response({
                "message": "Return request submitted successfully.",
                "order_status": order.order_status,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CODCheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        orders_data = request.data.get("orders", [])
        if not orders_data:
            return Response({"error": "No orders provided"}, status=400)

        # If single order, convert to list
        if isinstance(orders_data, dict):
            orders_data = [orders_data]

        product_ids = [order["product"] for order in orders_data]

        # Fetch all products at once
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        total_amount = 0
        order_objs = []

        if len(orders_data) == 1:
            # Single product order - avoid loop
            order_data = orders_data[0]
            product = product_map.get(order_data["product"])
            if not product:
                return Response(
                    {"error": f'Product {order_data["product"]} not found'}, status=404
                )
            if product.product_stock < order_data.get("quantity", 1):
                return Response(
                    {"error": f"Not enough stock for {product.name}"}, status=400
                )

            quantity = order_data.get("quantity", 1)
            price = product.price
            total_amount = price * quantity

            order_obj = Order(
                user=request.user,
                product=product,
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                shipping_address=order_data.get("shipping_address", ""),
                phone=order_data.get("phone", ""),
                payment_method="COD",
            )
            order_objs.append(order_obj)
        else:
            # Multiple product order
            for order_data in orders_data:
                product = product_map.get(order_data["product"])
                if not product:
                    return Response(
                        {"error": f'Product {order_data["product"]} not found'},
                        status=404,
                    )
                if product.product_stock < order_data.get("quantity", 1):
                    return Response(
                        {"error": f"Not enough stock for {product.name}"}, status=400
                    )

                quantity = order_data.get("quantity", 1)
                price = product.price
                total_amount += price * quantity

                order_objs.append(
                    Order(
                        user=request.user,
                        product=product,
                        quantity=quantity,
                        price=price,
                        total_amount=price * quantity,
                        shipping_address=order_data.get("shipping_address", ""),
                        phone=order_data.get("phone", ""),
                        payment_method="COD",
                    )
                )

        with transaction.atomic():
            # Bulk create orders
            orders = Order.objects.bulk_create(order_objs)

            # Bulk update stock
            for order in orders:
                Product.objects.filter(id=order.product.id).update(
                    product_stock=F("product_stock") - order.quantity
                )

            # Bulk delete cart items
            Cart.objects.filter(user=request.user, product_id__in=product_ids).delete()

        serializer = CheckoutOrderSerializer(orders, many=True)
        return Response(
            {
                "message": "Orders placed successfully (COD)",
                "total_amount": total_amount,
                "orders": serializer.data,
            },
            status=201,
        )


class RazorpayCheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        orders_data = request.data.get("orders", [])
        if not orders_data:
            return Response({"error": "No orders provided"}, status=400)

        total_amount = 0
        for order_data in orders_data:
            product = Product.objects.get(id=order_data["product"])
            if product.product_stock < order_data["quantity"]:
                return Response(
                    {"error": f"Not enough stock for {product.name}"}, status=400
                )
            total_amount += product.price * order_data["quantity"]

        amount_paise = int(total_amount * 100)
        razorpay_order = razorpay_client.order.create(
            {"amount": amount_paise, "currency": "INR", "payment_capture": 1}
        )

        return Response(
            {
                "message": "Razorpay order created",
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": amount_paise,
                "currency": "INR",
                "orders_payload": orders_data,
            },
            status=201,
        )


class RazorpayVerifyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get("razorpay_payment_id")
        order_id = request.data.get("razorpay_order_id")
        signature = request.data.get("razorpay_signature")
        orders_payload = request.data.get("orders_payload", [])

        if not orders_payload:
            return Response({"error": "No order data provided"}, status=400)

        # Step 1: Verify Razorpay signature
        try:
            razorpay_client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            )
        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Payment verification failed"}, status=400)

        # Step 2: Prepare products and orders
        if isinstance(orders_payload, dict):
            orders_payload = [orders_payload]  # handle single order

        product_ids = [o["product"] for o in orders_payload]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        total_amount = 0
        order_objs = []

        for order_data in orders_payload:
            product = product_map.get(order_data["product"])
            if not product:
                return Response(
                    {"error": f'Product {order_data["product"]} not found'}, status=404
                )
            if product.product_stock < order_data.get("quantity", 1):
                return Response(
                    {"error": f"Not enough stock for {product.name}"}, status=400
                )

            quantity = order_data.get("quantity", 1)
            price = product.price
            total_amount += price * quantity

            order_objs.append(
                Order(
                    user=request.user,
                    product=product,
                    quantity=quantity,
                    price=price,
                    total_amount=price * quantity,
                    shipping_address=order_data.get("shipping_address", ""),
                    phone=order_data.get("phone", ""),
                    payment_method="RAZORPAY",
                    payment_status="PAID",
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                )
            )

        with transaction.atomic():
            # Step 3: Bulk create orders
            orders = Order.objects.bulk_create(order_objs)

            # Step 4: Bulk reduce stock
            for order in orders:
                Product.objects.filter(id=order.product.id).update(
                    product_stock=F("product_stock") - order.quantity
                )

            # Step 5: Bulk delete cart items
            Cart.objects.filter(user=request.user, product_id__in=product_ids).delete()

        serializer = CheckoutOrderSerializer(orders, many=True)
        return Response(
            {
                "message": "Payment successful, orders created",
                "total_amount": total_amount,
                "orders": serializer.data,
            },
            status=201,
        )


class UpdateOrderAddressView(generics.UpdateAPIView):
    serializer_class = UserOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "order_id"

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user, order_status__in=["PENDING", "PROCESSING"]
        )

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        shipping_address = request.data.get("shipping_address")

        if not shipping_address:
            return Response(
                {"error": "Shipping address is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.shipping_address = shipping_address
        order.save()
        return Response(self.get_serializer(order).data)


class NotificationViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    List all notifications for a user and allow updating (mark as read)
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def perform_update(self, serializer):
        """
        Only allow updating the 'read' field
        """
        serializer.save()
