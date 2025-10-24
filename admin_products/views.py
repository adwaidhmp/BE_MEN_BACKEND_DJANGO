from django.db.models import Q
from product.models import Product
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from .serializer import AdminProductSerializer


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class AdminProductListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all()

        search_query = self.request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        category_filter = self.request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(category__id=category_filter)

        sort_param = self.request.query_params.get("sort")
        if sort_param == "stock_low_high":
            queryset = queryset.order_by("product_stock")
        elif sort_param == "stock_high_low":
            queryset = queryset.order_by("-product_stock")
        elif sort_param == "out_of_stock":
            queryset = queryset.filter(product_stock=0)
        elif sort_param == "newest":
            queryset = queryset.order_by("-created_at")
        elif sort_param == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort_param == "name_asc":
            queryset = queryset.order_by("name")
        elif sort_param == "name_desc":
            queryset = queryset.order_by("-name")
        elif sort_param == "price_low_high":
            queryset = queryset.order_by("price")
        elif sort_param == "price_high_low":
            queryset = queryset.order_by("-price")
        else:
            queryset = queryset.order_by("-created_at")  # Default: newest first

        return queryset


class AdminProductDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminProductSerializer
    queryset = Product.objects.all()
    lookup_field = "id"


class AdminProductCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminProductSerializer


class AdminProductUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminProductSerializer
    queryset = Product.objects.all()
    lookup_field = "id"


class AdminProductDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "id"
