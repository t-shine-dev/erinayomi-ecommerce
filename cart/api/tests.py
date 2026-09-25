from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from catalog.models import Product

from ..models import Cart, CartItem


class CartAPITests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Cart Ring",
            product_type=Product.ProductType.RING,
            price=Decimal("50000.00"),
            sku="RING-001",
            stock=5,
        )
        self.user = User.objects.create_user(
            username="cart-user",
            email="cart@example.com",
            password="test-password",
        )

    def test_anonymous_cart_can_add_and_update_items(self):
        add_url = reverse("cart_api:cart-item-list")
        response = self.client.post(
            add_url,
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cart"]["item_count"], 2)
        item_id = response.data["item"]["id"]

        update = self.client.patch(
            reverse("cart_api:cart-item-detail", kwargs={"pk": item_id}),
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["quantity"], 3)

        cart = self.client.get(reverse("cart_api:cart-detail"))
        self.assertEqual(cart.status_code, 200)
        self.assertEqual(Decimal(cart.data["subtotal"]), Decimal("150000.00"))

        removed = self.client.delete(
            reverse("cart_api:cart-item-detail", kwargs={"pk": item_id})
        )
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(CartItem.objects.exists())

    def test_anonymous_cart_merges_into_authenticated_cart(self):
        self.client.post(
            reverse("cart_api:cart-item-list"),
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("cart_api:cart-detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_authenticated_cart"])
        self.assertEqual(response.data["item_count"], 2)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_cart_items_are_scoped_to_current_authenticated_user(self):
        self.client.force_authenticate(self.user)
        self.client.post(
            reverse("cart_api:cart-item-list"),
            {"product_id": self.product.id, "quantity": 1},
            format="json",
        )

        other_user = User.objects.create_user(
            username="other-cart-user",
            email="other-cart@example.com",
            password="test-password",
        )
        self.client.force_authenticate(other_user)
        response = self.client.get(reverse("cart_api:cart-detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["item_count"], 0)