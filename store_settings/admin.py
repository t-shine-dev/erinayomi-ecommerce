from django.contrib import admin

from .models import NewsletterSubscriber, StoreSettings


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Business Info", {"fields": ("business_name", "logo", "business_email", "phone_number", "whatsapp_number")}),
        ("Location & Hours", {"fields": ("address", "business_hours")}),
        ("Social Links", {"fields": ("facebook_link", "instagram_link", "tiktok_link")}),
        ("Delivery", {"fields": ("delivery_fee", "free_shipping_threshold")}),
        ("Policies", {"fields": ("shipping_policy", "return_policy", "privacy_policy")}),
    )

    def has_add_permission(self, request):
        # Block creating a second row - this is a singleton.
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at", "is_active")
    list_filter = ("is_active",)
    search_fields = ("email",)
