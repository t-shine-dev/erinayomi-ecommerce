import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from orders.models import Order
from wishlist.models import Wishlist

from .forms import RegisterForm, EmailAuthenticationForm
from .models import EmailOTP, SavedAddress

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            
            # Security safeguard: Ensure newly registered users are strictly regular customers, never staff or admins
            user.is_staff = False
            user.is_superuser = False
            
            user.save()

            # Log the user in instantly and redirect them home
            login(request, user)
            messages.success(request, f"Welcome to ERINAYOMI, {user.first_name or user.email}!")
            return redirect("catalog:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
        
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        is_staff_requested = request.POST.get("is_staff_login") == "on"
        
        if form.is_valid():
            user = form.get_user()
            
            # Case 1: User checked "Login as Staff" but the account is NOT staff
            if is_staff_requested and not user.is_staff:
                messages.error(request, "This account is not authorized for staff access.")
                return render(request, "accounts/login.html", {"form": form})
                
            # Case 2: User IS staff, but did NOT check the "Login as Staff" box
            if user.is_staff and not is_staff_requested:
                messages.error(request, "Staff members must check 'Login as Staff' to access management features.")
                return render(request, "accounts/login.html", {"form": form})
                
            # Case 3: Regular customer login
            if not user.is_staff and not is_staff_requested:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.email}!")
                return redirect("catalog:home")
                
            # Case 4: Valid staff login
            if user.is_staff and is_staff_requested:
                login(request, user)
                messages.success(request, "Welcome to the ERINAYOMI Orders Control Room.")
                return redirect("orders:manager_dashboard")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm(request)
        
    return render(request, "accounts/login.html", {"form": form})

# --- Password Reset Flow Views ---

def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            messages.success(request, 'If an account exists with this email, instructions have been handled.')
            return redirect('accounts:login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            
    return render(request, 'accounts/password_reset_request.html')


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)[:10]
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return render(
        request,
        "accounts/profile.html",
        {"orders": orders, "wishlist_count": wishlist_count},
    )


@login_required
def profile_settings(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        user.phone_number = request.POST.get("phone_number", "").strip()
        user.address = request.POST.get("address", "").strip()
        user.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile_settings")
    return render(request, "accounts/settings.html")


@login_required
def address_book(request):
    if request.method == "POST":
        SavedAddress.objects.create(
            user=request.user,
            label=request.POST.get("label", "Home").strip() or "Home",
            full_name=request.POST.get("full_name", "").strip(),
            phone_number=request.POST.get("phone_number", "").strip(),
            address_line=request.POST.get("address_line", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            is_default=bool(request.POST.get("is_default")),
        )
        messages.success(request, "Address saved.")
        return redirect("accounts:address_book")

    addresses = SavedAddress.objects.filter(user=request.user)
    return render(request, "accounts/address_book.html", {"addresses": addresses})


@login_required
def delete_address(request, address_id):
    if request.method != "POST":
        return redirect("accounts:address_book")
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    address.delete()
    messages.info(request, "Address removed.")
    return redirect("accounts:address_book")


@login_required
def set_default_address(request, address_id):
    if request.method != "POST":
        return redirect("accounts:address_book")
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f"{address.label} set as default address.")
    return redirect("accounts:address_book")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("catalog:home")