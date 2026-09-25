from rest_framework import serializers

from catalog.api.serializers import ProductImageSerializer
from catalog.models import Product
from store_settings.models import StoreSettings

from ..models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    primary_image = ProductImageSerializer(read_only=True)
    current_price = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "primary_image",
            "current_price",
            "in_stock",
        )
        read_only_fields = fields

    def get_current_price(self, obj):
        return obj.current_price

    def get_in_stock(self, obj):
        return obj.in_stock


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal", "added_at")
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.subtotal


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(is_active=True),
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, product):
        if not product.in_stock:
            raise serializers.ValidationError(f"{product.name} is out of stock.")
        return product


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def update(self, instance, validated_data):
        instance.quantity = validated_data["quantity"]
        instance.save(update_fields=["quantity"])
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    shipping_fee = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    is_authenticated_cart = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "id",
            "items",
            "subtotal",
            "shipping_fee",
            "total",
            "item_count",
            "is_authenticated_cart",
            "updated_at",
        )
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.total

    def get_shipping_fee(self, obj):
        subtotal = obj.total
        return StoreSettings.load().shipping_fee_for(subtotal)

    def get_total(self, obj):
        subtotal = obj.total
        return subtotal + self.get_shipping_fee(obj)

    def get_item_count(self, obj):
        return obj.item_count

    def get_is_authenticated_cart(self, obj):
        return obj.user_id is not None