from rest_framework import serializers

from catalog.api.serializers import ProductListSerializer
from catalog.models import Product

from ..models import Wishlist


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ("id", "product", "added_at")
        read_only_fields = fields


class WishlistCreateSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
    )

    def validate_product_id(self, product):
        request = self.context["request"]
        if Wishlist.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError("This product is already in your wishlist.")
        return product