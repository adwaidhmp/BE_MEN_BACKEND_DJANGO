from product.models import Product
from product.serializer import ProductSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly


# Create your views here.
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
        # list → /api/products/

        # Returns a list of all products (from the queryset).

        # retrieve → /api/products/<id>/

        # Returns a single product by ID.
        