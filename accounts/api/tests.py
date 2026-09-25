from django.urls import reverse
from rest_framework.test import APITestCase

from ..models import SavedAddress, User


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="account-user",
            email="account@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-account-user",
            email="other-account@example.com",
            password="test-password",
        )

    def test_profile_requires_authentication_and_updates_current_user(self):
        url = reverse("accounts_api:me")
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            url,
            {"first_name": "Temitope", "phone_number": "08000000000"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Temitope")

    def test_saved_addresses_are_owned_and_default_address_is_preserved(self):
        self.client.force_authenticate(self.user)
        url = reverse("accounts_api:address-list")
        payload = {
            "label": "Home",
            "full_name": "Account User",
            "phone_number": "08000000000",
            "address_line": "1 Lagos Street",
            "city": "Lagos",
            "state": "Lagos",
            "is_default": True,
        }
        first = self.client.post(url, payload, format="json")
        second = self.client.post(
            url,
            {**payload, "label": "Office", "address_line": "2 Office Road"},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(
            SavedAddress.objects.filter(user=self.user, is_default=True).count(),
            1,
        )

        other_address = SavedAddress.objects.create(
            user=self.other_user,
            full_name="Other",
            phone_number="08000000001",
            address_line="Other Road",
        )
        response = self.client.get(
            reverse(
                "accounts_api:address-detail",
                kwargs={"pk": other_address.pk},
            )
        )
        self.assertEqual(response.status_code, 404)