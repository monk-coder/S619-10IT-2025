from django import forms
from .models import Task


class CitySearchForm(forms.Form):
    city = forms.CharField(label='Город', max_length=100)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['city', 'text', 'remind_on']
        widgets = {'remind_on': forms.DateTimeInput(attrs={'type': 'datetime-local'})}