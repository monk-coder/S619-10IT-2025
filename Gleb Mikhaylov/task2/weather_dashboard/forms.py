from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import WeatherTask


class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации пользователя"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'username',
            'email',
            'password1',
            'password2',
            Submit('submit', 'Зарегистрироваться', css_class='btn btn-primary')
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class WeatherTaskForm(forms.ModelForm):
    """Форма для создания и редактирования задач"""
    
    class Meta:
        model = WeatherTask
        fields = ['title', 'description', 'city', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Например: Взять зонт'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Дополнительные детали...'}),
            'city': forms.TextInput(attrs={'placeholder': 'Город'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'title': 'Название задачи',
            'description': 'Описание',
            'city': 'Город',
            'priority': 'Приоритет',
            'due_date': 'Срок выполнения',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            Row(
                Column('city', css_class='form-group col-md-6 mb-0'),
                Column('priority', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'due_date',
            Submit('submit', 'Сохранить', css_class='btn btn-primary')
        )


class WeatherSearchForm(forms.Form):
    """Форма для поиска погоды"""
    city = forms.CharField(
        max_length=100,
        label='Город',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите название города',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('city', css_class='form-group col-md-8 mb-0'),
                Column(Submit('submit', 'Поиск', css_class='btn btn-primary'), css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            )
        )
