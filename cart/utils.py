from .models import Cart


def get_or_create_cart(request):
    """Returns the Cart tied to the logged-in user, or to the anonymous session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge in any items added while the user was still anonymous.
        session_key = request.session.session_key
        if session_key:
            anon_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
            if anon_cart and anon_cart.pk != cart.pk:
                for item in anon_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                anon_cart.delete()
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart
