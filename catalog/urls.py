from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("products/<slug:slug>/review/", views.add_review, name="add_review"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
    path("tailoring/", views.tailoring, name="tailoring"),
    path("api/search-suggestions/", views.search_suggestions, name="search_suggestions"),
]
