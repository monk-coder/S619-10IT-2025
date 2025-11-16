from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import WeatherTask


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru'
        }),
        label='Электронная почта:'
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Придумайте имя пользователя'
        }),
        label='Имя пользователя:'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Не менее 8 символов'
        }),
        label='Пароль:'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтвердите пароль:'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class WeatherTaskForm(forms.ModelForm):
    class Meta:
        model = WeatherTask
        fields = ['title', 'description', 'related_city']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название задачи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите описание задачи',
                'rows': 3
            }),
            'related_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Необязательно'
            }),
        }
        labels = {
            'title': 'Название задачи',
            'description': 'Описание',
            'related_city': 'Связанный город',
        }


class CitySearchForm(forms.Form):
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите город...'
        }),
        label=''
    )