from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalog.urls")),
    path("accounts/", include("accounts.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("payments/", include("payments.urls")),
    path("store/", include("store_settings.urls")),
    path(
        "api/v1/",
        include(("catalog.api.urls", "catalog_api"), namespace="catalog_api"),
    ),
    path(
        "api/v1/",
        include(("accounts.api.urls", "accounts_api"), namespace="accounts_api"),
    ),
    path(
        "api/v1/",
        include(("cart.api.urls", "cart_api"), namespace="cart_api"),
    ),
    path(
        "api/v1/",
        include(("wishlist.api.urls", "wishlist_api"), namespace="wishlist_api"),
    ),
    path(
        "api/v1/",
        include(("orders.api.urls", "orders_api"), namespace="orders_api"),
    ),
]

admin.site.site_header = "ERINAYOMI Admin"
admin.site.site_title = "ERINAYOMI Admin"
admin.site.index_title = "Store Management"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
