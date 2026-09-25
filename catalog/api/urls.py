from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ProductReviewListCreateAPIView,
    ProductViewSet,
    TailoringAppointmentCreateAPIView,
)

app_name = "catalog_api"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "products/<slug:product_slug>/reviews/",
        ProductReviewListCreateAPIView.as_view(),
        name="product-review-list",
    ),
    path(
        "tailoring/appointments/",
        TailoringAppointmentCreateAPIView.as_view(),
        name="tailoring-appointment-list",
    ),
]