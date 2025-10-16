
from django.contrib import admin
from .models import Product,ProductCategory
from Be_men_user.models import Order


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category')
    search_fields = ('category',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'old_price', 'product_stock', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name', 'category__category', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_display_links = ('name',)



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'payment_status', 'order_status', 'tracking_id', 'delivery_date', 'created_at')
    list_filter = ('payment_status', 'order_status', 'created_at')
    search_fields = ('user__username', 'product__name', 'tracking_id', 'razorpay_order_id')

    readonly_fields = (
        'user', 'product', 'quantity', 'price', 'total_amount',
        'razorpay_order_id', 'razorpay_payment_id', 
        'payment_status', 'created_at', 'updated_at'
    )

    fields = (
        'user', 'product', 'quantity', 'price', 'total_amount',
        'payment_status', 'order_status', 'tracking_id', 'delivery_date',
        'shipping_address', 'phone',
        'razorpay_order_id', 'razorpay_payment_id', 
        'created_at', 'updated_at',
    )