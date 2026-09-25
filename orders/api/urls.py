from django.urls import path

from .views import OrderDetailAPIView, OrderHistoryAPIView

app_name = "orders_api"

urlpatterns = [
    path("orders/", OrderHistoryAPIView.as_view(), name="order-list"),
    path(
        "orders/<str:order_number>/",
        OrderDetailAPIView.as_view(),
        name="order-detail",
    ),
]