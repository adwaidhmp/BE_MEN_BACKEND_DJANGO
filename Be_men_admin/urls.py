from admin_orders.views import (AdminOrderDetailView, AdminOrderListView,
                                ReturnedCancelledOrdersView,ApproveReturnView)
from admin_products.views import (AdminProductCreateView,
                                  AdminProductDeleteView,
                                  AdminProductDetailView, AdminProductListView,
                                  AdminProductUpdateView)
from admin_users.views import (AdminBanUserView, AdminUserDetailView,
                               AdminUserListView)
from django.urls import path

from .views import AdminDashboardAPIView

urlpatterns = [
    path("dashboard/", AdminDashboardAPIView.as_view(), name="admin-dashboard"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("user/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("user/<int:pk>/ban/", AdminBanUserView.as_view(), name="admin-ban-user"),
    path("orders/", AdminOrderListView.as_view(), name="admin-order-list"),
    path("orders/<int:pk>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
    path("products/", AdminProductListView.as_view(), name="admin-product-list"),
    path("products/add/", AdminProductCreateView.as_view(), name="admin-product-add"),
    path(
        "products/<int:id>/",
        AdminProductDetailView.as_view(),
        name="admin-product-detail",
    ),
    path(
        "products/<int:id>/update/",
        AdminProductUpdateView.as_view(),
        name="admin-product-update",
    ),
    path(
        "products/<int:id>/delete/",
        AdminProductDeleteView.as_view(),
        name="admin-product-delete",
    ),
    path("returned-cancelled-orders/", ReturnedCancelledOrdersView.as_view(), name="cancelled-orders"),
    path('orders/<int:order_id>/return/', ApproveReturnView.as_view(), name='approve-return'),
]
