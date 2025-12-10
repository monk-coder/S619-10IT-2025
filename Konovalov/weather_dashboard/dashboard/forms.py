from django import forms
from .models import WeatherTask

class TaskForm(forms.ModelForm):
    class Meta:
        model = WeatherTask
        fields = ['city', 'task_text']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'task_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание задачи', 'rows': 3}),
        }
        labels = {
            'city': 'Город',
            'task_text': 'Задача',
        }