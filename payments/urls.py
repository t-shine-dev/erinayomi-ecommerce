from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("webhook/", views.paystack_webhook, name="webhook"),
    path("callback/", views.paystack_callback, name="callback"),
]