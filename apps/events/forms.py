from django import forms
from .models import Event
from .models import Event, Category, Registration, Comment, Like, Review, Favorite

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'image', 
            'start_datetime', 'end_datetime', 'location',
            'category',  # теперь одно поле, а не categories
            'price', 'is_free', 'max_participants'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),  # выпадающий список
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'title': 'Название мероприятия',
            'description': 'Описание',
            'image': 'Афиша',
            'start_datetime': 'Дата и время начала',
            'end_datetime': 'Дата и время окончания',
            'location': 'Место проведения',
            'category': 'Категория',
            'price': 'Цена (руб)',
            'is_free': 'Бесплатное мероприятие',
            'max_participants': 'Максимум участников',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Напишите комментарий...'}),
        }
        labels = {
            'text': '',
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'text')
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Ваш отзыв...'}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Текст отзыва (необязательно)',
        }