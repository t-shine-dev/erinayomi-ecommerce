from django.urls import path

from .views import WishlistItemDeleteAPIView, WishlistListCreateAPIView

app_name = "wishlist_api"

urlpatterns = [
    path("wishlist/", WishlistListCreateAPIView.as_view(), name="wishlist-list"),
    path(
        "wishlist/items/<int:product_id>/",
        WishlistItemDeleteAPIView.as_view(),
        name="wishlist-item-delete",
    ),
]