from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Product
from store_settings.models import StoreSettings

from .models import CartItem
from .utils import get_or_create_cart


def cart_detail(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related("product").prefetch_related("product__images")
    store = StoreSettings.load()
    estimated_shipping = store.shipping_fee_for(cart.total)
    amount_to_free_shipping = None
    if store.free_shipping_threshold and cart.total < store.free_shipping_threshold:
        amount_to_free_shipping = store.free_shipping_threshold - cart.total
    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "cart_items": cart_items,
        "estimated_shipping": estimated_shipping,
        "estimated_total": cart.total + estimated_shipping,
        "amount_to_free_shipping": amount_to_free_shipping,
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)

    quantity = request.POST.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    if not product.in_stock:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect(request.META.get("HTTP_REFERER", "catalog:home"))

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save()

    messages.success(request, f"Added {product.name} to your cart.")
    return redirect("cart:cart_detail")


def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    if request.method == "POST":
        quantity = request.POST.get("quantity", 1)
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity <= 0:
            item.delete()
            messages.info(request, "Item removed from cart.")
        else:
            item.quantity = quantity
            item.save()
            messages.success(request, "Cart updated.")

    return redirect("cart:cart_detail")


def remove_from_cart(request, item_id):
    if request.method != "POST":
        return redirect("cart:cart_detail")
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect("cart:cart_detail")
