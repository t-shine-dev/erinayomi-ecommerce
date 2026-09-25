from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SavedAddress, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone_number", "is_staff", "date_joined")
    search_fields = ("username", "email", "phone_number")
    fieldsets = UserAdmin.fieldsets + (
        ("Store profile", {"fields": ("phone_number", "address")}),
    )


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "full_name", "city", "state", "is_default")
    search_fields = ("user__username", "full_name", "city")
    list_filter = ("is_default",)
