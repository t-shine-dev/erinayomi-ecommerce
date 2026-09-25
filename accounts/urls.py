from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    
    # Custom 6-Digit Password Reset URLs
    path("password-reset/", views.password_reset_request_view, name="password_reset"),
    path("password-reset/verify/", views.password_reset_verify_view, name="password_reset_verify"),
    path("password-reset/confirm/", views.password_reset_confirm_view, name="password_reset_confirm"),

    path("profile/", views.profile, name="profile"),
    path("profile/settings/", views.profile_settings, name="profile_settings"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/password/change/done/",
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
    path("addresses/", views.address_book, name="address_book"),
    path("addresses/<int:address_id>/delete/", views.delete_address, name="delete_address"),
    path("addresses/<int:address_id>/default/", views.set_default_address, name="set_default_address"),
]