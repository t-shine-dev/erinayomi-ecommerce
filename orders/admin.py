from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "bell", "order_number", "full_name", "phone_number", "item_summary",
        "payment_badge", "delivery_date", "delivery_time", "total", "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone_number", "paystack_reference")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "paystack_reference", "created_at", "updated_at")
    fieldsets = (
        ("New Order", {
            "fields": ("order_number", "status", "created_at"),
        }),
        ("Customer", {
            "fields": ("user", "full_name", "email", "phone_number"),
        }),
        ("Delivery", {
            "fields": ("delivery_method", "shipping_address", "city", "state", "delivery_date", "delivery_time", "order_notes"),
        }),
        ("Payment", {
            "fields": ("subtotal", "shipping_fee", "total", "paystack_reference"),
        }),
    )

    @admin.display(description="")
    def bell(self, obj):
        if obj.status == Order.Status.PENDING:
            return format_html('<span title="Awaiting payment">🔔</span>')
        return ""

    @admin.display(description="Products x Qty")
    def item_summary(self, obj):
        return ", ".join(f"{i.product_name} x{i.quantity}" for i in obj.items.all()[:3]) or "—"

    @admin.display(description="Payment Status")
    def payment_badge(self, obj):
        colors = {
            "pending": "#B45309", "paid": "#047857", "processing": "#1D4ED8",
            "shipped": "#7C3AED", "delivered": "#047857", "cancelled": "#B91C1C",
        }
        color = colors.get(obj.status, "#111827")
        return format_html(
            '<span style="background:{}20;color:{};padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;">{}</span>',
            color, color, obj.get_status_display(),
        )
