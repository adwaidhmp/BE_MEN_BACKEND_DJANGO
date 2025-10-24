from rest_framework import serializers


class CategorySalesSerializer(serializers.Serializer):
    category = serializers.CharField(
        source="product__category__category", allow_null=True
    )
    total = serializers.DecimalField(max_digits=12, decimal_places=2)


# Serializer for monthly revenue chart
class MonthlyRevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


# Serializer for weekly revenue chart
class WeeklyRevenueSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


# Serializer for yearly revenue chart
class YearlyRevenueSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class AdminDashboardSerializer(serializers.Serializer):
    # Revenue & Orders
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    todays_orders = serializers.IntegerField()
    todays_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    weekly_orders = serializers.IntegerField()
    weekly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_orders = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    yearly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Products & Users
    total_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    total_users = serializers.IntegerField()

    # Order statuses
    orders_pending = serializers.IntegerField()
    orders_cancelled = serializers.IntegerField()
    orders_shipped = serializers.IntegerField()
    orders_delivered = serializers.IntegerField()

    # Category-wise sales
    sales_by_category = CategorySalesSerializer(many=True)

    # Revenue charts
    monthly_revenue_chart = MonthlyRevenueSerializer(many=True)
    weekly_revenue_chart = WeeklyRevenueSerializer(many=True)
    yearly_revenue_chart = YearlyRevenueSerializer(many=True)
