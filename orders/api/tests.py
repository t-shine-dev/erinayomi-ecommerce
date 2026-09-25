from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from catalog.models import Product

from ..models import Order, OrderItem


class OrdersAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="order-user",
            email="order@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-order-user",
            email="other-order@example.com",
            password="test-password",
        )
        product = Product.objects.create(
            name="Order Accessory",
            product_type=Product.ProductType.ACCESSORY,
            price=Decimal("45000.00"),
            sku="ORDER-001",
            stock=2,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Order User",
            email="order@example.com",
            phone_number="08000000000",
            shipping_address="1 Order Road",
            city="Lagos",
            state="Lagos",
            subtotal=Decimal("45000.00"),
            shipping_fee=Decimal("0.00"),
            total=Decimal("45000.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name=product.name,
            price=product.current_price,
            quantity=1,
        )
        self.other_order = Order.objects.create(
            user=self.other_user,
            full_name="Other User",
            email="other-order@example.com",
            phone_number="08000000001",
            shipping_address="Other Road",
            subtotal=Decimal("10000.00"),
            shipping_fee=Decimal("0.00"),
            total=Decimal("10000.00"),
        )

    def test_order_history_requires_authentication_and_is_scoped(self):
        url = reverse("orders_api:order-list")
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["order_number"],
            self.order.order_number,
        )

    def test_order_detail_cannot_be_read_by_another_user(self):
        self.client.force_authenticate(self.user)
        own = self.client.get(
            reverse(
                "orders_api:order-detail",
                kwargs={"order_number": self.order.order_number},
            )
        )
        other = self.client.get(
            reverse(
                "orders_api:order-detail",
                kwargs={"order_number": self.other_order.order_number},
            )
        )

        self.assertEqual(own.status_code, 200)
        self.assertEqual(
            Decimal(own.data["items"][0]["subtotal"]),
            Decimal("45000.00"),
        )
        self.assertEqual(other.status_code, 404)