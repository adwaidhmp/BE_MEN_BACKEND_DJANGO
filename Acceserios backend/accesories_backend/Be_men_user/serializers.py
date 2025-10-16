from rest_framework import serializers
from .models import User, Wishlist, Cart ,Order
from django.contrib.auth.password_validation import validate_password


class UserSignupSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # confirm password

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'profile_picture', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn’t match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            phone_number=validated_data.get('phone_number'),
            profile_picture=validated_data.get('profile_picture', 'default.png'),
            password=validated_data['password']
        )



class UserLoginSerializer(serializers.Serializer):
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone_number', 'profile_picture']
        read_only_fields = ['email']



class PasswordChangeSerializer(serializers.Serializer):
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    

from rest_framework import serializers
from Be_men_admin.models import Product, ProductCategory

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'category']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()  
    product_image = serializers.ImageField(use_url=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'description',
            'price',
            'old_price',
            'product_stock',
            'active',
            'product_image',
            'created_at',
            'updated_at',
        ]

class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity']


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = Wishlist
        fields = ['id', 'product']
        
        
class UserOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'product',
            'quantity',
            'price',
            'total_amount',
            'payment_status',
            'order_status',
            'tracking_id',
            'delivery_date',
            'shipping_address',
            'phone',
            'created_at'
        ]
        read_only_fields = [
            'payment_status',
            'tracking_id',
            'delivery_date',
            'price',
            'total_amount'
            'created_at',
            'order_status'
        ]
        
        

#user buying serializer
class CheckoutOrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Order
        fields = [
            'product',
            'quantity',
            'shipping_address',
            'phone',
            'total_amount',
            'payment_method',
        ]
        read_only_fields = [ 'total_amount','price']

    def create(self, validated_data):
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)
        
        # Assign unit price from product
        price = product.price  
        total_amount = price * quantity

        order = Order.objects.create(
            user=self.context['request'].user,
            product=product,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            shipping_address=validated_data.get('shipping_address', ''),
            phone=validated_data.get('phone', ''),
            payment_method=validated_data.get('payment_method', 'COD')
        )
        return order