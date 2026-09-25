from django.urls import path

from .views import (
    CartItemDetailAPIView,
    CartItemListCreateAPIView,
    CurrentCartAPIView,
)

app_name = "cart_api"

urlpatterns = [
    path("cart/", CurrentCartAPIView.as_view(), name="cart-detail"),
    path("cart/items/", CartItemListCreateAPIView.as_view(), name="cart-item-list"),
    path(
        "cart/items/<int:pk>/",
        CartItemDetailAPIView.as_view(),
        name="cart-item-detail",
    ),
]