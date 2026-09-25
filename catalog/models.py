import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        JEWELRY = "jewelry", "Jewelry"
        RING = "ring", "Ring"
        WATCH = "watch", "Watch"
        TAILORING = "tailoring", "Tailoring"
        ACCESSORY = "accessory", "Fashion Accessory"

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    product_type = models.CharField(
        max_length=20, choices=ProductType.choices, default=ProductType.ACCESSORY
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional. If set, this is shown as the selling price.",
    )
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["product_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.sku}")
            self.slug = base_slug
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percent(self):
        if self.is_on_sale and self.price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_new(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=14)

    @property
    def average_rating(self):
        if hasattr(self, "avg_rating_annotated"):
            return round(self.avg_rating_annotated or 0, 1)
        agg = self.reviews.aggregate(avg=models.Avg("rating"))
        return round(agg["avg"] or 0, 1)

    @property
    def review_count(self):
        if hasattr(self, "review_count_annotated"):
            return self.review_count_annotated
        return self.reviews.count()

    @property
    def primary_image(self):
        images = list(self.images.all())
        for img in images:
            if img.is_primary:
                return img
        return images[0] if images else None

    @property
    def secondary_image(self):
        images = list(self.images.all())
        return images[1] if len(images) > 1 else None

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def clean(self):
        super().clean()
        # Enforce a maximum limit of 5 images per product
        if not self.pk and self.product_id:
            if self.product.images.count() >= 5:
                raise ValidationError("A product cannot have more than 5 images.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} rated {self.product} {self.rating}/5"


class TailoringAppointment(models.Model):
    class ServiceType(models.TextChoices):
        AGBADA = "agbada", "Agbada / Native Wear"
        KAFTAN = "kaftan", "Kaftan"
        SUIT = "suit", "Suit"
        ALTERATION = "alteration", "Alteration"
        OTHER = "other", "Other / Custom"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    service_type = models.CharField(max_length=20, choices=ServiceType.choices, default=ServiceType.OTHER)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.CharField(max_length=50, blank=True)
    completion_date = models.DateField(
        null=True, blank=True, help_text="When the customer needs the finished piece by."
    )
    inspiration_image = models.ImageField(
        upload_to="tailoring/inspiration/", blank=True, null=True,
        help_text="Optional style reference photo uploaded by the customer.",
    )

    measurement_chest = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    measurement_waist = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    measurement_hip = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    measurement_shoulder = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    measurement_sleeve = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    measurement_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    measurements_notes = models.TextField(
        blank=True, help_text="Additional notes, or 'need help taking measurements'."
    )
    reference_notes = models.TextField(blank=True, help_text="Style references, fabric preference, occasion.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.get_service_type_display()}"
        