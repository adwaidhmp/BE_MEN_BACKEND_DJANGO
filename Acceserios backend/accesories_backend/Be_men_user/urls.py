from django.urls import path,include
from .views import SignupView, LoginView, LogoutView, ProfileView, ProfileUpdateView, PasswordChangeView
from .views import ForgotPasswordView, ResetPasswordView
from rest_framework.routers import DefaultRouter
from product.views import ProductViewSet
from wishlist.views import WishlistAPIView 
from cart.views import CartAPIView
from order.views import CheckoutAPIView, UserOrdersAPIView,RazorpayVerifyAPIView


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
from .views import RefreshTokenView

urlpatterns = [
    # User registration
    path("signup/", SignupView.as_view(), name="register"),

    # Login / Logout
    path("login/", LoginView.as_view(), name="login"),
    #token refresh
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path("logout/", LogoutView.as_view(), name="logout"),

    # User profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),

    # Password change
    path("profile/passwordchange/", PasswordChangeView.as_view(), name="password-change"),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password'),
    
    #product full and retirve one
    path('', include(router.urls)),
    
    # ---------- Wishlist ----------
    # GET: list wishlist
    # POST: add item (product_id in body)
    # DELETE: remove item (product_id in body OR URL)
    path('wishlist/', WishlistAPIView.as_view(), name='wishlist'),
    path('wishlist/<int:product_id>/', WishlistAPIView.as_view(), name='wishlist-detail'),

    # ---------- Cart ----------
    # GET: list cart
    # POST: add item (product_id + quantity in body)
    # DELETE: remove item (product_id in body OR URL)
    path('cart/', CartAPIView.as_view(), name='cart'),
    path('cart/<int:product_id>/', CartAPIView.as_view(), name='cart-detail'),
    
    
    path('my-orders/', UserOrdersAPIView.as_view(), name='user-orders'),
    path('orders/<int:order_id>/', UserOrdersAPIView.as_view(), name='order-detail'),
    path('my-orders/<int:order_id>/', UserOrdersAPIView.as_view(), name='delete-order'),
    path('checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('razorpay/verify/', RazorpayVerifyAPIView.as_view(), name='razorpay-verify'),
]



