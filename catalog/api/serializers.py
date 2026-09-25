from rest_framework import serializers

from ..models import (
    Category,
    Product,
    ProductImage,
    Review,
    TailoringAppointment,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description")
        read_only_fields = fields


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("id", "image_url", "alt_text", "is_primary", "order")
        read_only_fields = fields

    def get_image_url(self, obj):
        if not obj.image:
            return ""
        try:
            url = obj.image.url
        except ValueError:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    primary_image = ProductImageSerializer(read_only=True)
    current_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "product_type",
            "category",
            "primary_image",
            "price",
            "discount_price",
            "current_price",
            "is_on_sale",
            "discount_percent",
            "in_stock",
            "is_featured",
            "average_rating",
            "review_count",
            "created_at",
        )
        read_only_fields = fields

    def get_current_price(self, obj):
        return obj.current_price

    def get_is_on_sale(self, obj):
        return obj.is_on_sale

    def get_discount_percent(self, obj):
        return obj.discount_percent

    def get_in_stock(self, obj):
        return obj.in_stock

    def get_average_rating(self, obj):
        return obj.average_rating

    def get_review_count(self, obj):
        return obj.review_count


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "reviewer_name", "rating", "comment", "created_at")
        read_only_fields = ("id", "reviewer_name", "created_at")

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    description = serializers.CharField(read_only=True)
    sku = serializers.CharField(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "description",
            "sku",
            "images",
            "reviews",
        )


class TailoringAppointmentSerializer(serializers.ModelSerializer):
    inspiration_image = serializers.ImageField(
        required=False,
        allow_null=True,
        write_only=True,
    )
    inspiration_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TailoringAppointment
        fields = (
            "id",
            "full_name",
            "email",
            "phone_number",
            "service_type",
            "preferred_date",
            "preferred_time",
            "completion_date",
            "inspiration_image",
            "inspiration_image_url",
            "measurement_chest",
            "measurement_waist",
            "measurement_hip",
            "measurement_shoulder",
            "measurement_sleeve",
            "measurement_length",
            "measurements_notes",
            "reference_notes",
            "status",
            "created_at",
        )
        read_only_fields = (
            "id",
            "inspiration_image_url",
            "status",
            "created_at",
        )

    def get_inspiration_image_url(self, obj):
        if not obj.inspiration_image:
            return ""
        try:
            url = obj.inspiration_image.url
        except ValueError:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url