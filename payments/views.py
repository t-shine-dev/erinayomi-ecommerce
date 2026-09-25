import hashlib
import hmac
import json
import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from orders.models import Order


@csrf_exempt
def paystack_webhook(request):
    """Optional but recommended: configure this URL in your Paystack dashboard
    (Settings > API Keys & Webhooks) so payments are confirmed even if the
    customer closes their browser before the redirect completes."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    signature = request.headers.get("x-paystack-signature", "")
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"), request.body, hashlib.sha512
    ).hexdigest()
    if not hmac.compare_digest(signature, computed):
        return HttpResponseBadRequest("Invalid signature")

    event = json.loads(request.body)
    if event.get("event") == "charge.success":
        reference = event["data"]["reference"]
        amount_paid = event["data"]["amount"] / 100
        order = Order.objects.filter(paystack_reference=reference).first()
        if order and float(order.total_price) == float(amount_paid):
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.PAID
                order.save(update_fields=["status"])

    return HttpResponse(status=200)


def paystack_callback(request):
    # Paystack can return either 'reference' or 'trxref' depending on the payment channel
    reference = request.GET.get("reference") or request.GET.get("trxref")
    
    if not reference:
        messages.error(request, "No transaction reference provided.")
        return redirect("cart:cart_detail")

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    # Strictly query Paystack API to verify the real transaction state
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)

    if response.status_code == 200:
        res_data = response.json()
        if res_data.get("status") and res_data.get("data"):
            tx_status = res_data["data"]["status"]  # e.g., 'success', 'abandoned', 'pending', 'failed'
            
            if tx_status == "success":
                amount_paid = res_data["data"]["amount"] / 100
                order = Order.objects.filter(paystack_reference=reference).first()
                
                if order:
                    if float(order.total_price) == float(amount_paid):
                        if order.status == Order.Status.PENDING:
                            order.status = Order.Status.PAID
                            order.save(update_fields=["status"])
                        
                        messages.success(request, "Payment verified and successful!")
                        return redirect("orders:order_success", order_id=order.id)
                    else:
                        messages.error(request, "Payment amount mismatch detected.")
                        return redirect("cart:cart_detail")
            else:
                # The payment was abandoned, pending, or failed (user didn't pay)
                messages.error(request, f"Payment was not completed. Status: {tx_status}")
                return redirect("cart:cart_detail")

    messages.error(request, "Payment verification failed with Paystack.")
    return redirect("cart:cart_detail")