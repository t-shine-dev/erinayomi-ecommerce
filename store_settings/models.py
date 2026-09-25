from django.conf import settings as django_settings
from django.db import models


class StoreSettings(models.Model):
    """Singleton model: only one row (pk=1) ever exists. Edit it from /admin/."""

    business_name = models.CharField(max_length=200, default="ERINAYOMI")
    business_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Digits only, with country code, e.g. 2348012345678",
    )
    logo = models.ImageField(upload_to="store/", blank=True, null=True)
    address = models.TextField(blank=True)
    business_hours = models.CharField(max_length=200, blank=True)
    facebook_link = models.URLField(blank=True)
    instagram_link = models.URLField(blank=True)
    tiktok_link = models.URLField(blank=True)

    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Flat delivery fee in Naira, charged when the order is below the free shipping threshold.",
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Orders at or above this amount ship free. Leave blank to always charge the delivery fee.",
    )
    return_policy = models.TextField(blank=True, help_text="Shown on the policies page.")
    shipping_policy = models.TextField(blank=True, help_text="Shown on the policies page.")
    privacy_policy = models.TextField(blank=True, help_text="Shown on the policies page.")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store Settings"
        verbose_name_plural = "Store Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton row is never deletable from the admin

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "business_email": getattr(django_settings, "DEFAULT_STORE_EMAIL", ""),
                "whatsapp_number": getattr(django_settings, "DEFAULT_WHATSAPP_NUMBER", ""),
            },
        )
        return obj

    @property
    def whatsapp_link(self):
        if not self.whatsapp_number:
            return ""
        clean_number = "".join(filter(str.isdigit, str(self.whatsapp_number)))
        return f"https://wa.me/{clean_number}?text=Hi%20ERINAYOMI%2C%20I%27d%20like%20to%20ask%20about..."

    @property
    def mailto_link(self):
        return f"mailto:{self.business_email}" if self.business_email else ""

    def shipping_fee_for(self, subtotal):
        if self.free_shipping_threshold is not None and subtotal >= self.free_shipping_threshold:
            return 0
        return self.delivery_fee

    def __str__(self):
        return self.business_name


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email
