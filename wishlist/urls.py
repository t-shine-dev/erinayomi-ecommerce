from django.urls import path

from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.wishlist_view, name="wishlist"),
    path("toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
]
