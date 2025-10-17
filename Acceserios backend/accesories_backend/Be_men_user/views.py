from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSignupSerializer, UserProfileSerializer, PasswordChangeSerializer
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from Be_men_admin.models import Product
from .serializers import ProductSerializer



class SignupView(generics.CreateAPIView):
    
    serializer_class = UserSignupSerializer



class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({"detail": "Login successful"}, status=status.HTTP_200_OK)

            # Set cookies (HTTP dev-friendly)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,  # must be False for HTTP
                samesite="None", # works with same-origin
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="None",
            )
            return response
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)




class ProfileView(generics.RetrieveAPIView):
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    



class LogoutView(APIView):
    def post(self, request):
        response = Response({'detail': 'Logged out successfully'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response




class ProfileUpdateView(generics.UpdateAPIView):
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "Both old and new password required"}, status=400)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "Old password incorrect"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully"})

    



from django.contrib.auth import get_user_model

User = get_user_model()  # Use your custom user model

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists for security
            return Response(
                {'message': 'If an account with this email exists, a reset link has been sent.'},
                status=status.HTTP_200_OK
            )

        # Generate password reset token
        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Construct reset URL for frontend
        reset_url = f"http://localhost:5173/reset-password/{uidb64}/{token}/"

        # Send reset email
        send_mail(
            'Reset Your Password',
            f'Click the link below to reset your password:\n{reset_url}',
            'noreply@example.com',
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)
    




class ResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()

        return Response({'message': 'Password reset successfully!'}, status=status.HTTP_200_OK)






class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
        # list → /api/products/

        # Returns a list of all products (from the queryset).

        # retrieve → /api/products/<id>/

        # Returns a single product by ID.
        
        

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

class RefreshTokenView(APIView):

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'detail': 'Refresh token missing'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Verify and decode refresh token
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            # Create response with new access token
            response = Response({'access': new_access}, status=status.HTTP_200_OK)
            
            # Update access token cookie
            response.set_cookie(
                key="access_token",
                value=new_access,
                httponly=True,
                secure=True,       # True only in HTTPS
                samesite="None"      # "None" if cross-domain in HTTPS
            )
            return response

        except TokenError:
            return Response({'detail': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
from Be_men_user.models import Cart
from .serializers import CartSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Cart, Product
from .serializers import CartSerializer

class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all cart items with product details efficiently"""
        items = Cart.objects.filter(user=request.user).select_related('product').order_by('-added_at')
        serializer = CartSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to cart or update quantity"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
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
            deleted, _ = Cart.objects.filter(user=request.user, product_id=product_id).delete()
            if deleted:
                return Response({'message': 'Product removed from cart'}, status=204)
            return Response({'error': 'Product not found in cart'}, status=404)

        # No product_id → empty the cart
        Cart.objects.filter(user=request.user).delete()
        return Response({'message': 'All cart items removed'}, status=204)





from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from Be_men_user.models import Wishlist, Product
from .serializers import WishlistSerializer

class WishlistAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all cart items with product details efficiently"""
        items = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-added_at')
        serializer = WishlistSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to wishlist"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

        Wishlist.objects.get_or_create(user=request.user, product=product)
        return Response({'message': 'Product added to wishlist'}, status=200)

    def delete(self, request,product_id=None):
        """Remove a product from wishlist"""
        if product_id is not None:
            # Delete the specific product
            deleted, _ = Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
            if deleted:
                return Response({'message': 'Product removed from cart'}, status=204)
            return Response({'error': 'Product not found in cart'}, status=404)

        # No product_id → empty the cart
        Wishlist.objects.filter(user=request.user).delete()
        return Response({'message': 'All cart items removed'}, status=status.HTTP_204_NO_CONTENT)
    

from .models import Order
from .serializers import UserOrderSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

class UserOrdersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id=None):
        # If order_id is provided, return single order
        if order_id:
            try:
                order = Order.objects.select_related('product').get(id=order_id, user=request.user)
                serializer = UserOrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Otherwise, return all orders for the user
        orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')
        serializer = UserOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, order_id=None):
        if not order_id:
            return Response({'error': 'Order ID is required for delete'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status in ['SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED']:
            return Response({'error': 'Order cannot be cancelled at this stage'}, status=status.HTTP_400_BAD_REQUEST)

        order.order_status = 'CANCELLED'
        if order.payment_status == 'PAID':
            order.payment_status = 'REFUNDED'
            # Optional: trigger Razorpay refund here
        order.save()

        return Response({'message': 'Order cancelled successfully'}, status=status.HTTP_200_OK)
    



import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Order
from .serializers import CheckoutOrderSerializer

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class CheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        orders_data = request.data.get('orders', [])

        if not orders_data:
            return Response({'error': 'No orders provided'}, status=400)

        # Validate payment method and check stock
        for order_data in orders_data:
            pm = order_data.get('payment_method')
            if pm not in ['COD', 'RAZORPAY']:
                return Response(
                    {'error': f'Invalid payment method for product {order_data.get("product")}'},
                    status=400
                )

            product = Product.objects.get(id=order_data['product'])
            if product.product_stock < order_data['quantity']:
                return Response(
                    {'error': f'Not enough stock for {product.name}'},
                    status=400
                )

        # Serialize and save orders
        serializer = CheckoutOrderSerializer(
            data=orders_data,
            many=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        orders = serializer.save()

        # For COD, reduce stock immediately
        if orders_data[0]['payment_method'] == 'COD':
            for order in orders:
                product = order.product
                product.product_stock -= order.quantity
                product.save()

        # Calculate total_amount
        total_amount = sum(order.total_amount for order in orders)

        # Response
        if orders_data[0]['payment_method'] == 'COD':
            return Response({
                'message': 'Orders placed successfully (COD)',
                'total_amount': total_amount,
                'orders': CheckoutOrderSerializer(orders, many=True).data
            }, status=201)
        else:
            # Razorpay
            amount_paise = int(total_amount * 100)
            razorpay_order = razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1
            })

            # Attach Razorpay order ID to all orders
            for order in orders:
                order.razorpay_order_id = razorpay_order['id']
                order.save()

            return Response({
                'message': 'Razorpay order created',
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': amount_paise,
                'currency': 'INR',
                'orders': CheckoutOrderSerializer(orders, many=True).data
            }, status=201)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from django.conf import settings
import razorpay

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class RazorpayVerifyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')

        # Verify signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
        except razorpay.errors.SignatureVerificationError:
            # Payment failed → delete orders
            orders = Order.objects.filter(razorpay_order_id=order_id)
            deleted_count, _ = orders.delete()
            return Response({'error': f'Payment verification failed, {deleted_count} order(s) deleted'}, status=400)

        # Payment verified → mark as PAID & reduce stock
        orders = Order.objects.filter(razorpay_order_id=order_id)
        for order in orders:
            order.payment_status = 'PAID'
            order.razorpay_payment_id = payment_id
            order.save()

            # Reduce stock
            product = order.product
            product.product_stock -= order.quantity
            product.save()

        return Response({'message': 'Payment successful', 'orders': [o.id for o in orders]}, status=200)


