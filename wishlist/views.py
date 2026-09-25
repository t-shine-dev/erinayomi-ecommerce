from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Product

from .models import Wishlist
from .utils import get_wishlist_ids


@login_required
def wishlist_view(request):
    items = (
        Wishlist.objects.filter(user=request.user)
        .select_related("product")
        .prefetch_related("product__images")
    )
    # Annotate ratings on the related products in bulk (product_card.html reads these).
    product_ids = [i.product_id for i in items]
    rated_products = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids).annotate(
            avg_rating_annotated=Avg("reviews__rating"), review_count_annotated=Count("reviews", distinct=True)
        )
    }
    for item in items:
        if item.product_id in rated_products:
            item.product.avg_rating_annotated = rated_products[item.product_id].avg_rating_annotated
            item.product.review_count_annotated = rated_products[item.product_id].review_count_annotated

    return render(
        request,
        "wishlist/wishlist.html",
        {"items": items, "wishlist_ids": get_wishlist_ids(request)},
    )


@login_required
def toggle_wishlist(request, product_id):
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER", "wishlist:wishlist"))
    product = get_object_or_404(Product, pk=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, f"Removed {product.name} from your wishlist.")
    else:
        messages.success(request, f"Added {product.name} to your wishlist.")
    return redirect(request.META.get("HTTP_REFERER", "wishlist:wishlist"))
