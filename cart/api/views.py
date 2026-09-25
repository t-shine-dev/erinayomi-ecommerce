from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import Cart, CartItem
from ..utils import get_or_create_cart
from .serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)


def _load_cart(request):
    cart = get_or_create_cart(request)
    return Cart.objects.prefetch_related(
        "items__product__images",
    ).get(pk=cart.pk)


class CurrentCartAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CartSerializer

    def get_object(self):
        return _load_cart(self.request)


class CartItemListCreateAPIView(ListCreateAPIView):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CartItemCreateSerializer
        return CartItemSerializer

    def get_cart(self):
        return get_or_create_cart(self.request)

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.get_cart()).select_related(
            "product",
        ).prefetch_related("product__images")

    def create(self, request, *args, **kwargs):
        cart = self.get_cart()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])

        response_cart = _load_cart(request)
        response_item = response_cart.items.get(pk=item.pk)
        return Response(
            {
                "item": CartItemSerializer(
                    response_item,
                    context=self.get_serializer_context(),
                ).data,
                "cart": CartSerializer(
                    response_cart,
                    context=self.get_serializer_context(),
                ).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method in {"PATCH", "PUT"}:
            return CartItemUpdateSerializer
        return CartItemSerializer

    def get_queryset(self):
        cart = get_or_create_cart(self.request)
        return CartItem.objects.filter(cart=cart).select_related("product").prefetch_related(
            "product__images",
        )

    def update(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        serializer.save()
        item = self.get_queryset().get(pk=item.pk)
        return Response(
            CartItemSerializer(item, context=self.get_serializer_context()).data,
        )