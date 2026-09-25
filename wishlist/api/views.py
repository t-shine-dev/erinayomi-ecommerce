from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Wishlist
from .serializers import WishlistCreateSerializer, WishlistSerializer


class WishlistListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WishlistCreateSerializer
        return WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related(
            "product__category",
        ).prefetch_related("product__images")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = Wishlist.objects.create(
            user=request.user,
            product=serializer.validated_data["product"],
        )
        return Response(
            WishlistSerializer(item, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class WishlistItemDeleteAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, product_id):
        item = get_object_or_404(
            Wishlist,
            user=request.user,
            product_id=product_id,
        )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)