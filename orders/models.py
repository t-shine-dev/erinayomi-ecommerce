import uuid

from django.conf import settings
from django.db import models

from catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        PAID = "paid", "Paid"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class DeliveryMethod(models.TextChoices):
        DELIVERY = "delivery", "Home Delivery"
        PICKUP = "pickup", "Store Pickup"

    # Statuses shown in the customer-facing progress tracker, in order.
    TRACKER_STEPS = [Status.CONFIRMED, Status.PROCESSING, Status.SHIPPED, Status.DELIVERED]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    delivery_method = models.CharField(
        max_length=20, choices=DeliveryMethod.choices, default=DeliveryMethod.DELIVERY
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    delivery_date = models.DateField(null=True, blank=True, help_text="Requested/estimated delivery date.")
    delivery_time = models.CharField(
        max_length=50, blank=True, help_text="e.g. 'Morning (9am - 12pm)' or a specific time."
    )
    order_notes = models.TextField(blank=True, help_text="Special instructions from the customer.")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    paystack_reference = models.CharField(max_length=100, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ERY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def tracker_index(self):
        """Which tracker step (0-based) the order is currently at, or -1 if not yet
        confirmed/cancelled (still awaiting payment or cancelled)."""
        # Automatically map 'paid' status to the first step ('confirmed') index
        current_status = self.status
        if current_status == self.Status.PAID:
            current_status = self.Status.CONFIRMED

        try:
            return self.TRACKER_STEPS.index(current_status)
        except ValueError:
            return -1

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    