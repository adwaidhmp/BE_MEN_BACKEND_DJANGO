from Be_men_user.models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from order.models import Order
from product.models import Product, ProductCategory


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "name",
        "phone_number",
        "is_staff",
        "is_active",
        "is_superuser",
    )
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "name", "phone_number")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "phone_number", "profile_picture")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "phone_number",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category")
    search_fields = ("category",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "product_stock", "active")
    list_filter = ("category", "active")
    search_fields = ("name", "category__category", "description")
    readonly_fields = ("created_at", "updated_at")
    list_display_links = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "payment_status",
        "order_status",
        "tracking_id",
        "delivery_date",
        "created_at",
        'cancellation_reason',
        'return_reason'
    )
    list_filter = ("payment_status", "order_status", "created_at")
    search_fields = (
        "user__username",
        "product__name",
        "tracking_id",
        "razorpay_order_id",
    )

    readonly_fields = (
        "user",
        "product",
        "quantity",
        "price",
        "total_amount",
        "razorpay_order_id",
        "razorpay_payment_id",
        "payment_status",
        "created_at",
        "updated_at",
        "cancellation_reason",
        'return_reason'
    )

    fields = (
        "user",
        "product",
        "quantity",
        "price",
        "total_amount",
        "payment_status",
        "order_status",
        "tracking_id",
        "delivery_date",
        "shipping_address",
        "phone",
        "razorpay_order_id",
        "razorpay_payment_id",
        "created_at",
        "updated_at",
        "cancellation_reason",
        'return_reason'
    )
