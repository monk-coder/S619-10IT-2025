from django import forms
from .models import WeatherTask, UserProfile

class WeatherTaskForm(forms.ModelForm):
    city_name = forms.CharField(
        max_length=100,
        label='Город',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': 'Введите название города'
        })
    )
    task_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': 'Опишите задачу...',
            'rows': 4
        }),
        label='Задача'
    )

    class Meta:
        model = WeatherTask
        fields = ['city_name', 'task_text']

class LanguageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['language', 'theme']
        widgets = {
            'language': forms.Select(attrs={'class': 'form-select form-control-custom'}),
            'theme': forms.Select(attrs={'class': 'form-select form-control-custom'}),
        }
        labels = {
            'language': 'Язык интерфейса',
            'theme': 'Тема оформления',
        }