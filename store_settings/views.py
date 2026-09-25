import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import NewsletterSubscriber


def newsletter_subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
        else:
            already_subscribed = NewsletterSubscriber.objects.filter(email__iexact=email).exists()
            if not already_subscribed:
                NewsletterSubscriber.objects.create(email=email)
            if not already_subscribed:
                messages.success(request, "You're subscribed! Watch your inbox for new arrivals and offers.")
            else:
                messages.info(request, "You're already on the list.")
    return redirect(request.META.get("HTTP_REFERER", "catalog:home"))


def dashboard(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        messages.error(request, "Staff access only.")
        return redirect("accounts:login")

    from accounts.models import User
    from catalog.models import Product
    from orders.models import Order

    paid_statuses = [Order.Status.PAID, Order.Status.PROCESSING, Order.Status.SHIPPED, Order.Status.DELIVERED]
    paid_orders = Order.objects.filter(status__in=paid_statuses)

    revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
    orders_count = Order.objects.count()
    customers_count = User.objects.filter(is_staff=False).count()
    products_count = Product.objects.count()
    low_stock = Product.objects.filter(is_active=True, stock__lte=5).order_by("stock")[:8]
    pending_count = Order.objects.filter(status=Order.Status.PENDING).count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).order_by("-created_at")[:8]
    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:10]

    today = timezone.now().date()
    daily_revenue = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        total = paid_orders.filter(created_at__date=day).aggregate(total=Sum("total"))["total"] or 0
        daily_revenue.append({"label": day.strftime("%a"), "total": float(total)})
    max_daily = max([d["total"] for d in daily_revenue] or [1]) or 1
    for d in daily_revenue:
        d["pct"] = round((d["total"] / max_daily) * 100) if max_daily else 0

    context = {
        "revenue": revenue,
        "orders_count": orders_count,
        "customers_count": customers_count,
        "products_count": products_count,
        "low_stock": low_stock,
        "pending_orders": pending_orders,
        "pending_count": pending_count,
        "recent_orders": recent_orders,
        "daily_revenue": daily_revenue,
    }
    return render(request, "store_settings/dashboard.html", context)
