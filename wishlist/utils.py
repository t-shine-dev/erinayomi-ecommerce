from .models import Wishlist


def get_wishlist_ids(request):
    """Set of product IDs the current user has wishlisted (empty set if anonymous)."""
    if not request.user.is_authenticated:
        return set()
    return set(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))
