import random
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
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
            user.is_active = False  # Inactive until OTP verification
            user.save()

            # Create and send OTP
            otp_record = EmailOTP.objects.create(user=user, email=user.email)
            otp_record.generate_code()
            
            send_mail(
                subject='Your ERINAYOMI Verification Code',
                message=f'Your 6-digit verification code is: {otp_record.code}. It expires in 10 minutes.',
                from_email='noreply@erinayomi.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            request.session['verify_user_id'] = user.id
            messages.success(request, "Registration successful! Please check your email for the OTP code.")
            return redirect("accounts:verify_otp")
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


def verify_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect("accounts:register")
    
    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()
        try:
            otp_record = EmailOTP.objects.filter(user_id=user_id, is_verified=False).latest('created_at')
            if otp_record.is_expired():
                messages.error(request, "This OTP has expired. Please register again or request a new one.")
            elif otp_record.code == entered_code:
                otp_record.is_verified = True
                otp_record.save()
                
                # Activate user account and log them in
                user = User.objects.get(id=user_id)
                user.is_active = True
                user.save()
                
                login(request, user)
                del request.session['verify_user_id']
                messages.success(request, "Email verified successfully! Welcome to ERINAYOMI.")
                return redirect("catalog:home")
            else:
                messages.error(request, "Invalid OTP code. Please try again.")
        except EmailOTP.DoesNotExist:
            messages.error(request, "No active OTP request found.")
            
    return render(request, 'accounts/verify_otp.html')


# --- Password Reset Flow Views ---

def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            otp_record = EmailOTP.objects.create(user=user, email=user.email)
            otp_record.generate_code()
            
            send_mail(
                subject='Password Reset Verification Code',
                message=f'Your 6-digit password reset code is: {otp_record.code}. It expires in 10 minutes.',
                from_email='noreply@erinayomi.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            request.session['reset_user_id'] = user.id
            messages.success(request, 'A 6-digit verification code has been sent to your email.')
            return redirect('accounts:password_reset_verify')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            
    return render(request, 'accounts/password_reset_request.html')


def password_reset_verify_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()
        try:
            otp_record = EmailOTP.objects.filter(user_id=user_id, is_verified=False).latest('created_at')
            if otp_record.is_expired():
                messages.error(request, "This OTP has expired. Please request a new one.")
            elif otp_record.code == entered_code:
                otp_record.is_verified = True
                otp_record.save()
                
                request.session['reset_verified'] = True
                return redirect('accounts:password_reset_confirm')
            else:
                messages.error(request, "Invalid OTP code. Please try again.")
        except EmailOTP.DoesNotExist:
            messages.error(request, "No active OTP request found.")

    return render(request, 'accounts/password_reset_verify.html')


def password_reset_confirm_view(request):
    if not request.session.get('reset_verified') or not request.session.get('reset_user_id'):
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password and new_password == confirm_password:
            user_id = request.session.get('reset_user_id')
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_verified', None)
            
            messages.success(request, 'Your password has been successfully reset. You can now log in.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Passwords do not match or cannot be blank.')

    return render(request, 'accounts/password_reset_confirm.html')


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