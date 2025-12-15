from django import forms
from .models import UserNote

class NoteForm(forms.ModelForm):
    class Meta:
        model = UserNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок заметки'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите содержание заметки',
                'rows': 5
            }),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
        }