from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random


class User(AbstractUser):
    """Custom user utilizing email for authentication."""

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
            counter = 1
            base_username = self.username
            while User.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                self.username = f"{base_username}{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.email


class SavedAddress(models.Model):
    """A customer's address book entry, selectable at checkout."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_addresses")
    label = models.CharField(max_length=50, default="Home", help_text="e.g. Home, Office")
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            SavedAddress.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)

    def __str__(self):
        return f"{self.label} — {self.user}"


class EmailOTP(models.Model):
    """Temporary storage for email verification codes."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def generate_code(self):
        self.code = f"{random.randint(100000, 999999)}"
        self.save()

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)
    