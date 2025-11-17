from datetime import timedelta

from Be_men_user.models import User
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import ExtractWeek, ExtractYear, TruncMonth
from django.utils import timezone
from order.models import Order
from product.models import Product
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import AdminDashboardSerializer


class AdminDashboardAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()

        total_expr = ExpressionWrapper(
            F("price") * F("quantity"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        valid_orders = Order.objects.exclude(order_status__in=["CANCELLED", "RETURNED"])

        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
        start_of_month = start_of_day.replace(day=1)
        start_of_year = start_of_day.replace(month=1, day=1)

        agg_fields = {"revenue": Sum(total_expr), "orders": Count("id")}

        today_stats = valid_orders.filter(created_at__gte=start_of_day).aggregate(
            **agg_fields
        )
        week_stats = valid_orders.filter(created_at__gte=start_of_week).aggregate(
            **agg_fields
        )
        month_stats = valid_orders.filter(created_at__gte=start_of_month).aggregate(
            **agg_fields
        )
        year_stats = valid_orders.filter(created_at__gte=start_of_year).aggregate(
            **agg_fields
        )
        total_stats = valid_orders.aggregate(**agg_fields)

        total_products = Product.objects.exclude(product_stock__lte=0).count()
        out_of_stock = Product.objects.filter(product_stock__lte=0).count()
        total_users = User.objects.filter(is_staff=False).count()

        order_status_counts = Order.objects.values("order_status").annotate(
            count=Count("id")
        )
        status_dict = {i["order_status"]: i["count"] for i in order_status_counts}

        category_sales = (
            valid_orders.values("product__category__category")
            .annotate(total=Sum(total_expr))
            .order_by("-total")
        )

        # Monthly revenue this year
        monthly_data = (
            valid_orders.filter(created_at__year=now.year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(revenue=Sum(total_expr))
            .order_by("month")
        )
        monthly_revenue_chart = [
            {
                "month": item["month"].strftime("%B"),
                "revenue": float(item["revenue"] or 0),
            }
            for item in monthly_data
        ]

        # Weekly revenue this month
        weekly_data = (
            valid_orders.filter(created_at__year=now.year, created_at__month=now.month)
            .annotate(week=ExtractWeek("created_at"))
            .values("week")
            .annotate(revenue=Sum(total_expr))
            .order_by("week")
        )
        weekly_revenue_chart = [
            {"week": item["week"], "revenue": float(item["revenue"] or 0)}
            for item in weekly_data
        ]

        # Yearly revenue (all years)
        yearly_data = (
            valid_orders.annotate(year=ExtractYear("created_at"))
            .values("year")
            .annotate(revenue=Sum(total_expr))
            .order_by("year")
        )
        yearly_revenue_chart = [
            {"year": item["year"], "revenue": float(item["revenue"] or 0)}
            for item in yearly_data
        ]

        #  raw data dict
        raw_data = {
            "total_orders": total_stats["orders"] or 0,
            "total_revenue": total_stats["revenue"] or 0,
            "todays_orders": today_stats["orders"] or 0,
            "todays_revenue": today_stats["revenue"] or 0,
            "weekly_orders": week_stats["orders"] or 0,
            "weekly_revenue": week_stats["revenue"] or 0,
            "monthly_orders": month_stats["orders"] or 0,
            "monthly_revenue": month_stats["revenue"] or 0,
            "yearly_revenue": year_stats["revenue"] or 0,
            "total_products": total_products,
            "out_of_stock_products": out_of_stock,
            "total_users": total_users,
            "orders_pending": status_dict.get("PROCESSING", 0),
            "orders_cancelled": status_dict.get("CANCELLED", 0),
            "orders_shipped": status_dict.get("SHIPPED", 0),
            "orders_delivered": status_dict.get("DELIVERED", 0),
            "sales_by_category": list(category_sales),
            "monthly_revenue_chart": monthly_revenue_chart,
            "weekly_revenue_chart": weekly_revenue_chart,
            "yearly_revenue_chart": yearly_revenue_chart,
        }

        serializer = AdminDashboardSerializer(raw_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
