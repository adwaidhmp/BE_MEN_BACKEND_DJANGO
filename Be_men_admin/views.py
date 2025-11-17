from datetime import timedelta, date
import calendar
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import ExtractWeek, ExtractYear, TruncMonth
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from Be_men_user.models import User
from order.models import Order
from product.models import Product

from .serializer import AdminDashboardSerializer


class AdminDashboardAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()

        # total price expression (assumes Order has price & quantity fields or those fields are on the related item)
        total_expr = ExpressionWrapper(
            F("price") * F("quantity"),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )

        # Exclude cancelled/returned orders from revenue counts
        valid_orders = Order.objects.exclude(order_status__in=["CANCELLED", "RETURNED"])

        # Boundaries for day/week/month/year
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=start_of_day.weekday())  # Monday as start
        start_of_month = start_of_day.replace(day=1)
        # compute start_of_next_month to get month end
        if start_of_month.month == 12:
            start_of_next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
        else:
            start_of_next_month = start_of_month.replace(month=start_of_month.month + 1)
        end_of_month = start_of_next_month - timedelta(seconds=1)

        start_of_year = start_of_day.replace(month=1, day=1)

        agg_fields = {"revenue": Sum(total_expr), "orders": Count("id")}

        # Aggregates for different periods
        today_stats = valid_orders.filter(created_at__gte=start_of_day).aggregate(**agg_fields)
        week_stats = valid_orders.filter(created_at__gte=start_of_week).aggregate(**agg_fields)
        month_stats = valid_orders.filter(created_at__gte=start_of_month).aggregate(**agg_fields)
        year_stats = valid_orders.filter(created_at__gte=start_of_year).aggregate(**agg_fields)
        total_stats = valid_orders.aggregate(**agg_fields)

        # Basic counts
        total_products = Product.objects.exclude(product_stock__lte=0).count()
        out_of_stock = Product.objects.filter(product_stock__lte=0).count()
        total_users = User.objects.filter(is_staff=False).count()

        # Order status counts
        order_status_counts = Order.objects.values("order_status").annotate(count=Count("id"))
        status_dict = {i["order_status"]: i["count"] for i in order_status_counts}

        # Sales by category (top categories)
        category_sales = (
            valid_orders.values("product__category__category")
            .annotate(total=Sum(total_expr))
            .order_by("-total")
        )

        # -------------------------
        # Monthly revenue for THIS YEAR (all months Jan..Dec with zeros filled)
        # -------------------------
        monthly_data_qs = (
            valid_orders.filter(created_at__year=now.year)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(revenue=Sum(total_expr))
            .order_by("month")
        )
        # Map month (datetime) -> revenue
        monthly_map = {item["month"].month: Decimal(item["revenue"] or 0) for item in monthly_data_qs}

        monthly_revenue_chart = []
        for m in range(1, 13):
            month_name = calendar.month_name[m]
            revenue = float(monthly_map.get(m, Decimal(0)))
            monthly_revenue_chart.append({"month": month_name, "revenue": revenue})

        # -------------------------
        # Weekly revenue for THIS MONTH (all weeks that intersect the current month)
        # We'll compute all unique ISO week numbers that intersect the month, then aggregate.
        # -------------------------
        # build set of week numbers present in the month
        weeks_in_month = []
        # iterate through each day of month to collect week numbers and also compute week ranges
        year = start_of_month.year
        month = start_of_month.month
        _, days_in_month = calendar.monthrange(year, month)
        week_numbers_set = []
        for d in range(1, days_in_month + 1):
            current_day = date(year, month, d)
            # Python's isocalendar()[1] gives ISO week number
            week_no = current_day.isocalendar()[1]
            if week_no not in week_numbers_set:
                week_numbers_set.append(week_no)

        # Query weekly revenue restricted to this month range
        weekly_qs = (
            valid_orders.filter(created_at__gte=start_of_month, created_at__lte=end_of_month)
            .annotate(week=ExtractWeek("created_at"))
            .values("week")
            .annotate(revenue=Sum(total_expr))
            .order_by("week")
        )
        weekly_map = {int(item["week"]): Decimal(item["revenue"] or 0) for item in weekly_qs}

        weekly_revenue_chart = []
        for week_no in week_numbers_set:
            # compute approximate week start/end inside the month for label purposes
            # find all dates in the month with that week number
            week_dates = [
                date(year, month, d)
                for d in range(1, days_in_month + 1)
                if date(year, month, d).isocalendar()[1] == week_no
            ]
            if week_dates:
                week_start = week_dates[0]
                week_end = week_dates[-1]
            else:
                # fallback (shouldn't happen)
                week_start = start_of_month.date()
                week_end = min(end_of_month.date(), start_of_month.date() + timedelta(days=6))
            revenue = float(weekly_map.get(week_no, Decimal(0)))
            weekly_revenue_chart.append(
                {
                    "week_number": week_no,
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "revenue": revenue,
                }
            )

        # -------------------------
        # Yearly revenue (all years present in orders). We include any year with revenue.
        # -------------------------
        yearly_qs = (
            valid_orders.annotate(year=ExtractYear("created_at"))
            .values("year")
            .annotate(revenue=Sum(total_expr))
            .order_by("year")
        )
        # Make list of years and revenues (sorted)
        yearly_revenue_chart = []
        for item in yearly_qs:
            y = int(item["year"])
            yearly_revenue_chart.append({"year": y, "revenue": float(item["revenue"] or 0)})

        # -------------------------
        # Raw data dict (top-level numbers + charts)
        # -------------------------
        raw_data = {
            "total_orders": int(total_stats["orders"] or 0),
            "total_revenue": float(total_stats["revenue"] or 0),
            "todays_orders": int(today_stats["orders"] or 0),
            "todays_revenue": float(today_stats["revenue"] or 0),
            "weekly_orders": int(week_stats["orders"] or 0),
            "weekly_revenue": float(week_stats["revenue"] or 0),
            "monthly_orders": int(month_stats["orders"] or 0),
            "monthly_revenue": float(month_stats["revenue"] or 0),
            "yearly_revenue": float(year_stats["revenue"] or 0),
            "total_products": total_products,
            "out_of_stock_products": out_of_stock,
            "total_users": total_users,
            "orders_pending": int(status_dict.get("PROCESSING", 0)),
            "orders_cancelled": int(status_dict.get("CANCELLED", 0)),
            "orders_shipped": int(status_dict.get("SHIPPED", 0)),
            "orders_delivered": int(status_dict.get("DELIVERED", 0)),
            "sales_by_category": list(category_sales),
            "monthly_revenue_chart": monthly_revenue_chart,
            "weekly_revenue_chart": weekly_revenue_chart,
            "yearly_revenue_chart": yearly_revenue_chart,
        }

        serializer = AdminDashboardSerializer(raw_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
