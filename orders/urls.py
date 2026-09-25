from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.order_success, name="order_success"),
    path("history/", views.order_history, name="order_history"),
    path("manager/dashboard/", views.store_manager_dashboard, name="manager_dashboard"), # Put this BEFORE <str:order_number>
    path("<str:order_number>/", views.order_detail, name="order_detail"),
]