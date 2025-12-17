from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя',
                'autofocus': True
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пароль'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Подтверждение пароля'
            }),
        }
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем текст помощи для полей
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError('Имя пользователя должно содержать не менее 3 символов')
        return username

class TaskForm(forms.ModelForm):
    class Meta:
        from .models import WeatherTask
        model = WeatherTask
        fields = ['city', 'task_text']
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Город'
            }),
            'task_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Описание задачи (например: "Взять зонт, если будет дождь")',
                'rows': 3
            }),
        }
        labels = {
            'city': 'Город',
            'task_text': 'Задача',
        }
    
    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not city or len(city.strip()) < 2:
            raise forms.ValidationError('Введите корректное название города')
        return city.strip()
    
    def clean_task_text(self):
        task_text = self.cleaned_data.get('task_text')
        if not task_text or len(task_text.strip()) < 5:
            raise forms.ValidationError('Описание задачи должно содержать не менее 5 символов')
        return task_text.strip()