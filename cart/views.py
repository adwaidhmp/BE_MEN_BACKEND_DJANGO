from django.shortcuts import render
from product.models import Product
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart
from .serializer import CartSerializer


class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all cart items with product details efficiently"""
        items = (
            Cart.objects.filter(user=request.user)
            .select_related("product")
            .order_by("-added_at")
        )
        serializer = CartSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to cart or update quantity"""
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        cart_item, created = Cart.objects.get_or_create(
            user=request.user, product=product
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=200)

    def delete(self, request, product_id=None):
        """Remove a product from cart or empty the cart"""
        if product_id is not None:
            # Delete the specific product
            deleted, _ = Cart.objects.filter(
                user=request.user, product_id=product_id
            ).delete()
            if deleted:
                return Response({"message": "Product removed from cart"}, status=204)
            return Response({"error": "Product not found in cart"}, status=404)

        # No product_id → empty the cart
        Cart.objects.filter(user=request.user).delete()
        return Response({"message": "All cart items removed"}, status=204)
