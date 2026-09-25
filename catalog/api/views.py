from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.generics import CreateAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Category, Product, Review
from ..services import send_tailoring_notification
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
    TailoringAppointmentSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    lookup_field = "slug"


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        params = self.request.query_params
        products = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
            .annotate(
                avg_rating_annotated=Avg("reviews__rating"),
                review_count_annotated=Count("reviews", distinct=True),
            )
        )

        query = (params.get("search") or params.get("q") or "").strip()
        if query:
            products = products.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(sku__icontains=query)
            )

        category_slugs = params.getlist("category")
        if len(category_slugs) == 1 and "," in category_slugs[0]:
            category_slugs = [
                value.strip() for value in category_slugs[0].split(",") if value.strip()
            ]
        if category_slugs:
            products = products.filter(category__slug__in=category_slugs)

        product_type = params.get("product_type") or params.get("type")
        if product_type:
            products = products.filter(product_type=product_type)

        min_price = self._decimal_param(params.get("min_price"))
        max_price = self._decimal_param(params.get("max_price"))
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)

        min_rating = params.get("rating") or params.get("min_rating")
        if min_rating and min_rating.isdigit():
            products = products.filter(avg_rating_annotated__gte=int(min_rating))

        availability = params.get("availability")
        in_stock = params.get("in_stock")
        if availability == "in_stock" or in_stock in {"true", "1", "yes"}:
            products = products.filter(stock__gt=0)
        elif availability == "out_of_stock" or in_stock in {"false", "0", "no"}:
            products = products.filter(stock=0)

        if params.get("featured") in {"true", "1", "yes"}:
            products = products.filter(is_featured=True)

        if params.get("new") in {"true", "1", "yes"}:
            products = products.filter(
                created_at__gte=timezone.now() - timedelta(days=14)
            )

        ordering = params.get("ordering") or params.get("sort")
        ordering_map = {
            "price_asc": "price",
            "price_desc": "-price",
            "newest": "-created_at",
            "name": "name",
            "name_asc": "name",
            "-name": "-name",
            "rating": "-avg_rating_annotated",
            "-rating": "avg_rating_annotated",
            "price": "price",
            "-price": "-price",
            "created_at": "created_at",
            "-created_at": "-created_at",
        }
        products = products.order_by(ordering_map.get(ordering, "-created_at"))

        if self.action == "retrieve":
            products = products.prefetch_related("reviews__user")
        return products

    @staticmethod
    def _decimal_param(value):
        if not value:
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None


class ProductReviewListCreateAPIView(ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_product(self):
        return get_object_or_404(
            Product,
            slug=self.kwargs["product_slug"],
            is_active=True,
        )

    def get_queryset(self):
        return (
            Review.objects.filter(product=self.get_product())
            .select_related("user")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        product = self.get_product()
        if Review.objects.filter(product=product, user=request.user).exists():
            return Response(
                {"detail": "You have already reviewed this product."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(product=product, user=request.user)
        return Response(
            self.get_serializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class TailoringAppointmentCreateAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TailoringAppointmentSerializer

    def perform_create(self, serializer):
        appointment = serializer.save()
        send_tailoring_notification(appointment)