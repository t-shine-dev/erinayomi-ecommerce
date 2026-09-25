from .models import Cart


def cart(request):
    """Exposes `nav_cart` in every template for the navbar cart badge."""
    cart_obj = None
    if request.user.is_authenticated:
        cart_obj = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart_obj = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    return {"nav_cart": cart_obj}
