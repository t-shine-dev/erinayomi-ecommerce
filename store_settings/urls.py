from django.urls import path

from . import views

app_name = "store_settings"

urlpatterns = [
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
