from product.models import Product
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from wishlist.serializer import WishlistSerializer

from .models import Wishlist


class WishlistAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all cart items with product details efficiently"""
        items = (
            Wishlist.objects.filter(user=request.user)
            .select_related("product")
            .order_by("-added_at")
        )
        serializer = WishlistSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to wishlist"""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        Wishlist.objects.get_or_create(user=request.user, product=product)
        return Response({"message": "Product added to wishlist"}, status=200)

    def delete(self, request, product_id=None):
        """Remove a product from wishlist"""
        if product_id is not None:
            # Delete the specific product
            deleted, _ = Wishlist.objects.filter(
                user=request.user, product_id=product_id
            ).delete()
            if deleted:
                return Response({"message": "Product removed from cart"}, status=204)
            return Response({"error": "Product not found in cart"}, status=404)

        # No product_id → empty the cart
        Wishlist.objects.filter(user=request.user).delete()
        return Response(
            {"message": "All cart items removed"}, status=status.HTTP_204_NO_CONTENT
        )
