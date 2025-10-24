import math

from django_filters.rest_framework import (CharFilter, DjangoFilterBackend,
                                           FilterSet)
from product.models import Product
from product.serializer import ProductSerializer
from rest_framework import filters, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response


class ProductFilter(FilterSet):
    category = CharFilter(field_name="category__category", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["category"]


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count / self.page_size)
        return Response(
            {
                "total_items": self.page.paginator.count,
                "total_pages": total_pages,
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(active=True).order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ProductPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "category__category", "description"]
    ordering_fields = ["price"]
