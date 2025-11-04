from django.db.models import Q
from django.utils import timezone
from order.models import Order
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import AdminOrderSerializer, CancelledOrderSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminOrderListView(generics.ListAPIView):
    """
    View all orders (Admin only) with search, filter, sort, and pagination
    """

    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminOrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = Order.objects.select_related("user", "product").all()

        status_filter = self.request.query_params.get("order_status")
        payment_filter = self.request.query_params.get("payment_status")
        if status_filter:
            queryset = queryset.filter(order_status=status_filter.upper())
        if payment_filter:
            queryset = queryset.filter(payment_status=payment_filter.upper())

        search_query = self.request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(user__name__icontains=search_query)
                | Q(user__email__icontains=search_query)
            )

        sort_param = self.request.query_params.get("ordering")
        if sort_param in ["created_at", "-created_at"]:
            queryset = queryset.order_by(sort_param)
        else:
            queryset = queryset.order_by("-created_at")

        return queryset


class AdminOrderDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update an order's status, tracking ID, delivery date, or cancellation reason.
    """

    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminOrderSerializer
    queryset = Order.objects.all()

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Refresh the order instance to ensure latest data
        order.refresh_from_db()

        # --- If admin cancels order ---
        if order.order_status.upper() == "CANCELLED":
            # Only mark as refunded if the payment method is Razorpay
            if order.payment_method and order.payment_method.upper() == "RAZORPAY":
                order.payment_status = "REFUNDED"

            order.cancelled_at = timezone.now()

            # Save cancellation reason if provided
            reason = request.data.get("cancellation_reason")
            if reason:
                order.cancellation_reason = reason

            order.save(
                update_fields=["payment_status", "cancelled_at", "cancellation_reason"]
            )

        return Response(
            {
                "message": "Order updated successfully",
                "order": self.get_serializer(order).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ReturnedCancelledOrdersView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CancelledOrderSerializer

    def get_queryset(self):
        valid_statuses = ["CANCELLED", "RETURN_PENDING", "RETURNED"]
        qs = (
            Order.objects.select_related("user", "product")
            .filter(order_status__in=valid_statuses)
            .order_by("-updated_at")
        )

        # Filter by query param if provided
        order_type = self.request.query_params.get("type", "").upper()
        if order_type in valid_statuses:
            qs = qs.filter(order_status=order_type)

        return qs


class ApproveReturnView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if order.order_status != "RETURN_PENDING":
            return Response(
                {"detail": "This order is not pending return approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = request.data.get("action", "").lower()

        if action == "approve":
            # Update order status
            order.order_status = "RETURNED"
            order.returned_at = timezone.now()

            # Update stock
            if order.product:
                order.product.product_stock += order.quantity
                order.product.save()

            # Update payment status if Razorpay
            if order.payment_method == "RAZORPAY":
                order.payment_status = "REFUNDED"

            order.save()

            return Response(
                {
                    "message": "Return approved successfully. Stock and payment updated if applicable."
                },
                status=status.HTTP_200_OK,
            )

        elif action == "reject":
            order.order_status = "DELIVERED"
            order.save()
            return Response(
                {"message": "Return request rejected."}, status=status.HTTP_200_OK
            )

        else:
            return Response(
                {"detail": "Invalid action. Use 'approve' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
