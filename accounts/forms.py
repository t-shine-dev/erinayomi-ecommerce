from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

COUNTRY_PHONE_CODES = [
    ("+234", "NG (+234)"),
    ("+44", "GB (+44)"),
    ("+233", "GH (+233)"),
    ("+254", "KE (+254)"),
    ("+27", "ZA (+27)"),
    ("+1", "US (+1)"),
    ("+91", "IN (+91)"),
]

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=150, label="First Name")
    last_name = forms.CharField(required=True, max_length=150, label="Surname / Last Name")
    email = forms.EmailField(required=True)
    country_code = forms.ChoiceField(choices=COUNTRY_PHONE_CODES, initial="+234", label="Country Code")
    phone_number = forms.CharField(required=False, max_length=15, widget=forms.TextInput(attrs={'placeholder': '8012345678'}))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "country_code", "phone_number"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        code = self.cleaned_data.get('country_code', '')
        number = self.cleaned_data.get('phone_number', '').strip()
        
        if number:
            if number.startswith('0'):
                number = number[1:]
            user.phone_number = f"{code}{number}"
        else:
            user.phone_number = ""
            
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control'})
    )