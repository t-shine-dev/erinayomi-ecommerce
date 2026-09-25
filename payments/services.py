"""Thin wrapper around the Paystack Transactions API.

Docs: https://paystack.com/docs/api/transaction/
"""
import requests
from django.conf import settings

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    """Raised when Paystack rejects a request, is unreachable, or returns
    something we can't parse (network issue, outage, proxy/firewall block)."""


def _headers():
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "PAYSTACK_SECRET_KEY is not set. Add it to your .env file "
            "(get test keys from https://dashboard.paystack.com/#/settings/developer)."
        )
    return {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}


def _call(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=15, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise PaystackError(
            f"Paystack returned an unexpected response (HTTP {response.status_code}). "
            "This usually means a network/firewall issue, or Paystack is down - try again shortly."
        ) from exc

    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack rejected the request."))
    return data["data"]


def initialize_transaction(email, amount_naira, reference, callback_url):
    """Starts a transaction and returns Paystack's data dict, which includes
    `authorization_url` (redirect the customer here) and `reference`.

    amount_naira is converted to kobo, since Paystack's API expects the
    smallest currency unit.
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
    payload = {
        "email": email,
        "amount": int(round(float(amount_naira) * 100)),
        "reference": reference,
        "callback_url": callback_url,
    }
    return _call("post", url, headers=_headers(), json=payload)


def verify_transaction(reference):
    """Confirms a transaction actually succeeded. Always call this server-side
    before marking an order as paid - never trust the redirect alone."""
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    return _call("get", url, headers=_headers())
