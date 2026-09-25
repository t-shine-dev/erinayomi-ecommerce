from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User

from ..models import Category, Product, Review, TailoringAppointment


class CatalogAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Watches",
            slug="watches",
            description="Timepieces",
        )
        self.watch = Product.objects.create(
            category=self.category,
            name="Gold Watch",
            product_type=Product.ProductType.WATCH,
            price=Decimal("250000.00"),
            discount_price=Decimal("225000.00"),
            sku="WATCH-001",
            stock=4,
            is_featured=True,
        )
        self.out_of_stock = Product.objects.create(
            category=self.category,
            name="Sold Out Watch",
            product_type=Product.ProductType.WATCH,
            price=Decimal("300000.00"),
            sku="WATCH-002",
            stock=0,
        )
        self.user = User.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="test-password",
            first_name="Ada",
        )

    def test_categories_and_products_are_public(self):
        category_response = self.client.get(reverse("catalog_api:category-list"))
        product_response = self.client.get(reverse("catalog_api:product-list"))

        self.assertEqual(category_response.status_code, 200)
        self.assertEqual(product_response.status_code, 200)
        product = next(
            item
            for item in product_response.data["results"]
            if item["id"] == self.watch.id
        )
        self.assertEqual(Decimal(product["current_price"]), Decimal("225000.00"))
        self.assertTrue(product["in_stock"])
        self.assertNotIn("stock", product)

    def test_product_filters_ordering_and_pagination(self):
        for index in range(13):
            Product.objects.create(
                category=self.category,
                name=f"Additional Watch {index}",
                product_type=Product.ProductType.WATCH,
                price=Decimal("100000.00") + index,
                sku=f"EXTRA-{index:03d}",
                stock=2,
            )

        response = self.client.get(
            reverse("catalog_api:product-list"),
            {"product_type": "watch", "in_stock": "true", "ordering": "price"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 14)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertLessEqual(
            Decimal(response.data["results"][0]["current_price"]),
            Decimal(response.data["results"][1]["current_price"]),
        )

    def test_product_search_aliases_filter_name_description_and_sku(self):
        response = self.client.get(
            reverse("catalog_api:product-list"),
            {"q": "gold"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["results"]], [self.watch.id])

        sku_response = self.client.get(
            reverse("catalog_api:product-list"),
            {"search": self.watch.sku},
        )
        self.assertEqual(sku_response.status_code, 200)
        self.assertEqual(sku_response.data["count"], 1)
        self.assertEqual(sku_response.data["results"][0]["id"], self.watch.id)

    def test_product_detail_returns_not_found_for_unknown_slug(self):
        response = self.client.get(
            reverse("catalog_api:product-detail", kwargs={"slug": "missing-product"})
        )
        self.assertEqual(response.status_code, 404)

    def test_review_requires_authentication_and_is_owned_by_request_user(self):
        url = reverse(
            "catalog_api:product-review-list",
            kwargs={"product_slug": self.watch.slug},
        )
        unauthenticated = self.client.post(url, {"rating": 5, "comment": "Excellent"})
        self.assertEqual(unauthenticated.status_code, 403)

        self.client.force_authenticate(self.user)
        created = self.client.post(url, {"rating": 5, "comment": "Excellent"})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["reviewer_name"], "Ada")

        duplicate = self.client.post(url, {"rating": 4, "comment": "Again"})
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(Review.objects.count(), 1)

    @patch("catalog.api.views.send_tailoring_notification")
    def test_tailoring_appointment_validates_choices_and_creates_model(self, notify):
        url = reverse("catalog_api:tailoring-appointment-list")
        response = self.client.post(
            url,
            {
                "full_name": "Temitope Sunday",
                "email": "customer@example.com",
                "phone_number": "08000000000",
                "service_type": "agbada",
                "preferred_date": (timezone.now() + timedelta(days=7)).date(),
                "measurement_chest": "42.5",
                "reference_notes": "Deep navy fabric",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        appointment = TailoringAppointment.objects.get()
        self.assertEqual(appointment.service_type, "agbada")
        self.assertEqual(appointment.measurement_chest, Decimal("42.5"))
        notify.assert_called_once_with(appointment)

        invalid = self.client.post(
            url,
            {
                "full_name": "Customer",
                "email": "customer@example.com",
                "phone_number": "08000000000",
                "service_type": "not-a-service",
            },
            format="multipart",
        )
        self.assertEqual(invalid.status_code, 400)