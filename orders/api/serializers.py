from rest_framework import serializers

from ..models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product_name", "price", "quantity", "subtotal")
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.subtotal


class OrderListSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()
    delivery_method_label = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "order_number",
            "status",
            "status_label",
            "delivery_method",
            "delivery_method_label",
            "total",
            "item_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_status_label(self, obj):
        return obj.get_status_display()

    def get_delivery_method_label(self, obj):
        return obj.get_delivery_method_display()

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderDetailSerializer(OrderListSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracker_index = serializers.IntegerField(read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + (
            "full_name",
            "email",
            "phone_number",
            "shipping_address",
            "city",
            "state",
            "delivery_date",
            "delivery_time",
            "order_notes",
            "subtotal",
            "shipping_fee",
            "items",
            "tracker_index",
        )