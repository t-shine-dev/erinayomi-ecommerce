from django.urls import path

from .views import (
    CurrentUserAPIView,
    SavedAddressDetailAPIView,
    SavedAddressListCreateAPIView,
)

app_name = "accounts_api"

urlpatterns = [
    path("me/", CurrentUserAPIView.as_view(), name="me"),
    path(
        "me/addresses/",
        SavedAddressListCreateAPIView.as_view(),
        name="address-list",
    ),
    path(
        "me/addresses/<int:pk>/",
        SavedAddressDetailAPIView.as_view(),
        name="address-detail",
    ),
]