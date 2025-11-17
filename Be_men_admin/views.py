from datetime import timedelta

from Be_men_user.models import User
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.utils import timezone
from order.models import Order
from product.models import Product
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import calendar
from .serializer import AdminDashboardSerializer
from django.db.models.functions import TruncMonth, TruncWeek, ExtractYear
from datetime import timedelta


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

       # --- Charts: monthly (full year), weekly (this month by week), yearly (by year) ---

# 1) Monthly revenue for entire current year (guarantees Jan..Dec)
        monthly_qs = (
            valid_orders.filter(created_at__year=now.year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(revenue=Sum(total_expr))
            .order_by("month")
        )
        # map month index (0..11) -> revenue
        monthly_map = {m["month"].month - 1: float(m["revenue"] or 0) for m in monthly_qs}
        monthly_revenue_chart = []
        for i in range(12):
            month_name = calendar.month_name[i + 1]  # January .. December
            monthly_revenue_chart.append({
                "month_index": i,
                "month": month_name,
                "revenue": monthly_map.get(i, 0.0),
            })

        # 2) Weekly revenue for the current month (produce week ranges covering the month)
        # compute end_of_month
        last_day = calendar.monthrange(now.year, now.month)[1]
        end_of_month = start_of_month.replace(day=last_day)

        # annotate by week-start and aggregate
        weekly_qs = (
            valid_orders.filter(created_at__gte=start_of_month, created_at__lte=end_of_month)
            .annotate(week_start=TruncWeek("created_at"))
            .values("week_start")
            .annotate(revenue=Sum(total_expr))
            .order_by("week_start")
        )

        # build dict week_start_date -> revenue
        weekly_map = {}
        for item in weekly_qs:
            ws = item["week_start"]
            # ensure date object key (some DBs return datetime)
            ws_date = ws.date() if hasattr(ws, "date") else ws
            weekly_map[ws_date] = float(item["revenue"] or 0)

        # build list of week intervals that cover the whole month (Monday..Sunday)
        weeks = []
        # find the week start containing start_of_month (Monday start)
        cursor = (start_of_month - timedelta(days=start_of_month.weekday())).date()
        end_date = end_of_month.date()

        while cursor <= end_date:
            week_start = cursor
            week_end = cursor + timedelta(days=6)
            label_start = max(week_start, start_of_month.date())
            label_end = min(week_end, end_date)
            revenue = weekly_map.get(week_start, 0.0)
            weeks.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "label": f"{label_start.strftime('%b %d')} - {label_end.strftime('%b %d')}",
                "revenue": revenue,
            })
            cursor = cursor + timedelta(days=7)

        weekly_revenue_chart = weeks

        # 3) Yearly revenue by year (same idea as before)
        yearly_data = (
            valid_orders.annotate(year=ExtractYear("created_at"))
            .values("year")
            .annotate(revenue=Sum(total_expr))
            .order_by("year")
        )
        yearly_revenue_chart = [
            {"year": int(item["year"]), "revenue": float(item["revenue"] or 0)}
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
