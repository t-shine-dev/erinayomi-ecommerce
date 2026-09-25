from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart", null=True, blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @cached_property
    def total(self):
        return sum((item.subtotal for item in self.items.select_related("product")), 0)

    @cached_property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        owner = self.user.username if self.user else f"session:{self.session_key}"
        return f"Cart({owner})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def subtotal(self):
        return self.product.current_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
