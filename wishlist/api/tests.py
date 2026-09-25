from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from catalog.models import Product

from ..models import Wishlist


class WishlistAPITests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Wishlist Watch",
            product_type=Product.ProductType.WATCH,
            price=Decimal("125000.00"),
            sku="WISH-001",
            stock=1,
        )
        self.user = User.objects.create_user(
            username="wishlist-user",
            email="wishlist@example.com",
            password="test-password",
        )

    def test_wishlist_requires_authentication(self):
        response = self.client.get(reverse("wishlist_api:wishlist-list"))
        self.assertEqual(response.status_code, 403)

    def test_user_can_add_list_and_remove_own_wishlist_item(self):
        self.client.force_authenticate(self.user)
        list_url = reverse("wishlist_api:wishlist-list")

        created = self.client.post(
            list_url,
            {"product_id": self.product.id},
            format="json",
        )
        self.assertEqual(created.status_code, 201)

        duplicate = self.client.post(
            list_url,
            {"product_id": self.product.id},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)

        listed = self.client.get(list_url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data["results"]), 1)

        removed = self.client.delete(
            reverse(
                "wishlist_api:wishlist-item-delete",
                kwargs={"product_id": self.product.id},
            )
        )
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(Wishlist.objects.exists())

    def test_wishlist_delete_cannot_remove_another_users_item(self):
        other = User.objects.create_user(
            username="other-wishlist-user",
            email="other-wishlist@example.com",
            password="test-password",
        )
        Wishlist.objects.create(user=other, product=self.product)
        self.client.force_authenticate(self.user)

        response = self.client.delete(
            reverse(
                "wishlist_api:wishlist-item-delete",
                kwargs={"product_id": self.product.id},
            )
        )
        self.assertEqual(response.status_code, 404)