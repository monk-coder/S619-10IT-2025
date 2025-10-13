# dashboard/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import WeatherRule

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Логин'
        }),
        label='Логин'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Email'
        }),
        label='Email'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Пароль'
        }),
        label='Пароль'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Подтверждение пароля'
        }),
        label='Подтверждение пароля'
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        help_texts = {
            'username': None,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

class WeatherSearchForm(forms.Form):
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Введите город (например: Moscow, London, Tokyo)...'
        })
    )

class TaskForm(forms.Form):
    description = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'flex-1 px-3 py-2 border rounded',
            'placeholder': 'Например: Взять зонт, если дождь...'
        })
    )
    
    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if not description:
            raise forms.ValidationError("Описание задачи не может быть пустым")
        if len(description) < 5:
            raise forms.ValidationError("Описание должно содержать минимум 5 символов")
        return description

# dashboard/forms.py
class WeatherRuleForm(forms.ModelForm):
    class Meta:
        model = WeatherRule
        fields = ['name', 'condition_type', 'operator', 'threshold_value', 'task_description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Название правила'
            }),
            'condition_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'operator': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'threshold_value': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.1'
            }),
            'task_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Что сделать, когда условие выполнится?'
            }),
        }