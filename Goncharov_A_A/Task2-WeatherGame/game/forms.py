from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import MultipleObjectsReturned


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Неверный email или пароль.",
        "inactive": "Аккаунт отключён.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if not email or not password:
            return cleaned_data

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
        except (UserModel.DoesNotExist, MultipleObjectsReturned):
            raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")

        if not user.check_password(password):
            raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")

        if not user.is_active:
            raise forms.ValidationError(self.error_messages["inactive"], code="inactive")

        self._user = user
        return cleaned_data

    def get_user(self):
        return self._user
