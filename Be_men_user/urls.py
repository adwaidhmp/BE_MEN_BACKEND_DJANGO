from cart.views import CartAPIView
from django.urls import include, path
from order.views import (CODCheckoutAPIView, NotificationViewSet,
                         RazorpayCheckoutAPIView, RazorpayVerifyAPIView,
                         UpdateOrderAddressView, UserOrdersAPIView,ReturnRequestView)
from product.views import ProductViewSet
from rest_framework.routers import DefaultRouter
from wishlist.views import WishlistAPIView

from .views import (ForgotPasswordView, LoginView, LogoutView,
                    PasswordChangeView, ProfileUpdateView, ProfileView,
                    ResetPasswordView, SignupView)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"notifications", NotificationViewSet, basename="notifications")

urlpatterns = [
    # User registration
    path("signup/", SignupView.as_view(), name="register"),
    # Login / Logout
    path("login/", LoginView.as_view(), name="login"),
    # token refresh
    path("logout/", LogoutView.as_view(), name="logout"),
    # User profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    # Password change
    path(
        "profile/passwordchange/", PasswordChangeView.as_view(), name="password-change"
    ),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "reset-password/<uidb64>/<token>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    # product full and retirve one
    path("", include(router.urls)),
    # wishlist
    path("wishlist/", WishlistAPIView.as_view(), name="wishlist"),
    path(
        "wishlist/<int:product_id>/", WishlistAPIView.as_view(), name="wishlist-detail"
    ),
    # cart
    path("cart/", CartAPIView.as_view(), name="cart"),
    path("cart/<int:product_id>/", CartAPIView.as_view(), name="cart-detail"),
    # order
    path("my-orders/", UserOrdersAPIView.as_view(), name="user-orders"),
    path("orders/<int:order_id>/", UserOrdersAPIView.as_view(), name="order-detail"),
    path("my-orders/<int:order_id>/", UserOrdersAPIView.as_view(), name="delete-order"),
    path("checkout/cod/", CODCheckoutAPIView.as_view(), name="checkout-cod"),
    path(
        "checkout/razorpay/",
        RazorpayCheckoutAPIView.as_view(),
        name="checkout-razorpay",
    ),
    path(
        "checkout/razorpay/verify/",
        RazorpayVerifyAPIView.as_view(),
        name="razorpay-verify",
    ),
    path(
        "orders/<int:order_id>/update-address/",
        UpdateOrderAddressView.as_view(),
        name="update-order-address",
    ),
    path('orders/<int:order_id>/return/', ReturnRequestView.as_view(), name='return-request'),
]
