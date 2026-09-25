from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from cart.utils import get_or_create_cart
from payments.services import PaystackError, initialize_transaction, verify_transaction
from store_settings.models import StoreSettings

from .models import Order, OrderItem


def _send_order_confirmation_email(order):
    """Best-effort receipt email. Never blocks checkout if it fails."""
    try:
        body = render_to_string("orders/email/order_confirmation.txt", {"order": order})
        send_mail(
            subject=f"Your ERINAYOMI order {order.order_number} is confirmed",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )
    except Exception:
        pass


@login_required(login_url='/accounts/login/')
def checkout(request):
    cart = get_or_create_cart(request)
    store = StoreSettings.load()

    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    cart_items = list(cart.items.select_related("product").prefetch_related("product__images"))
    estimated_shipping = store.shipping_fee_for(cart.total)
    saved_addresses = (
        request.user.saved_addresses.all() if request.user.is_authenticated else None
    )
    context = {
        "cart": cart, "cart_items": cart_items,
        "estimated_shipping": estimated_shipping,
        "estimated_total": cart.total + estimated_shipping,
        "saved_addresses": saved_addresses,
    }

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        shipping_address = request.POST.get("shipping_address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        delivery_method = request.POST.get("delivery_method", Order.DeliveryMethod.DELIVERY)
        delivery_date = request.POST.get("delivery_date") or None
        delivery_time = request.POST.get("delivery_time", "").strip()
        order_notes = request.POST.get("order_notes", "").strip()

        if not all([full_name, email, phone_number, shipping_address]):
            messages.error(request, "Please fill in every field.")
            return render(request, "orders/checkout.html", context)

        # Confirm stock is still available before charging anyone.
        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.error(
                    request,
                    f"Only {item.product.stock} of {item.product.name} left in stock.",
                )
                return render(request, "orders/checkout.html", context)

        subtotal = cart.total
        shipping_fee = 0 if delivery_method == Order.DeliveryMethod.PICKUP else store.shipping_fee_for(subtotal)
        total = subtotal + shipping_fee

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=full_name,
                    email=email,
                    phone_number=phone_number,
                    shipping_address=shipping_address,
                    city=city,
                    state=state,
                    delivery_method=delivery_method,
                    delivery_date=delivery_date,
                    delivery_time=delivery_time,
                    order_notes=order_notes,
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    total=total,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        price=item.product.current_price,
                        quantity=item.quantity,
                    )
                    for item in cart_items
                ])

                callback_url = request.build_absolute_uri(reverse("orders:order_success"))
                data = initialize_transaction(
                    email=email,
                    amount_naira=total,
                    reference=order.order_number,
                    callback_url=callback_url,
                )
                order.paystack_reference = data.get("reference", order.order_number)
                order.save(update_fields=["paystack_reference"])
        except PaystackError as exc:
            # Rolled back by transaction.atomic() - no orphaned order is left behind.
            messages.error(request, f"Could not start payment: {exc}")
            return render(request, "orders/checkout.html", context)

        return redirect(data["authorization_url"])

    return render(request, "orders/checkout.html", context)


@login_required
def order_history(request):
    if request.user.is_staff:
        orders = Order.objects.all().order_by("-created_at")
    else:
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/order_history.html", {"orders": orders})


def order_detail(request, order_number):
    kwargs = {"order_number": order_number}
    if request.user.is_authenticated and request.user.is_staff:
        order = get_object_or_404(Order, **kwargs)
    elif request.user.is_authenticated:
        order = get_object_or_404(Order, **kwargs, user=request.user)
    else:
        order = get_object_or_404(Order, **kwargs, user__isnull=True)
    return render(request, "orders/order_detail.html", {"order": order})


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def store_manager_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, "orders/manager_dashboard.html", {"orders": orders})


def order_success(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")
    
    if not reference:
        messages.error(request, "No transaction reference provided.")
        return redirect("cart:cart_detail")

    order = get_object_or_404(Order, paystack_reference=reference)

    if order.status == Order.Status.PENDING:
        try:
            data = verify_transaction(reference)
            if data.get("status") == "success":
                order.status = Order.Status.PAID
                order.save(update_fields=["status"])
                
                # Reduce stock and empty the cart
                for item in order.items.select_related("product"):
                    if item.product:
                        item.product.stock = max(0, item.product.stock - item.quantity)
                        item.product.save(update_fields=["stock"])
                
                cart = get_or_create_cart(request)
                cart.items.all().delete()
                _send_order_confirmation_email(order)
            else:
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status"])
                messages.error(request, "Payment was not successful.")
                return redirect("cart:cart_detail")
        except PaystackError as exc:
            messages.error(request, f"Could not verify payment: {exc}")
            return redirect("cart:cart_detail")

    # If someone tries to view an order that is still not paid
    if order.status != Order.Status.PAID:
        messages.error(request, "This order has not been paid for yet.")
        return redirect("cart:cart_detail")

    return render(request, "orders/order_success.html", {"order": order})