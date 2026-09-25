from django.contrib import admin

from .models import Category, Product, ProductImage, Review, TailoringAppointment


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 5  # Restricts the admin inline view to a maximum of 5 image rows


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "product_type", "price", "discount_price",
        "stock", "is_active", "is_featured",
    )
    list_filter = ("product_type", "is_active", "is_featured", "category")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    list_editable = ("price", "discount_price", "stock", "is_active", "is_featured")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username")


@admin.register(TailoringAppointment)
class TailoringAppointmentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "service_type", "preferred_date", "completion_date", "status", "created_at")
    list_filter = ("status", "service_type")
    search_fields = ("full_name", "email", "phone_number")
    list_editable = ("status",)
    fieldsets = (
        ("Request", {"fields": ("status", "full_name", "email", "phone_number", "service_type")}),
        ("Scheduling", {"fields": ("preferred_date", "preferred_time", "completion_date")}),
        ("Measurements (inches)", {"fields": (
            "measurement_chest", "measurement_waist", "measurement_hip",
            "measurement_shoulder", "measurement_sleeve", "measurement_length",
            "measurements_notes",
        )}),
        ("Style", {"fields": ("inspiration_image", "reference_notes")}),
    )