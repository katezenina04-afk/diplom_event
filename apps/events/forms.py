from django import forms
from django.db import models
from django.conf import settings
from .models import Event, Category, Registration, Comment, Like, Review, Favorite

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'image',
            'start_datetime', 'end_datetime', 'location', 'venue_name',
            'external_url', 'venue_url', 'organizer_url',
            'category',
            'price', 'is_free', 'max_participants'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-control'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control'}),
            'venue_url': forms.URLInput(attrs={'class': 'form-control'}),
            'organizer_url': forms.URLInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
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
            'venue_name': 'Название площадки',
            'external_url': 'Внешняя ссылка',
            'venue_url': 'Сайт площадки',
            'organizer_url': 'Сайт организатора',
            'category': 'Категория',
            'price': 'Цена (руб)',
            'is_free': 'Бесплатное мероприятие',
            'max_participants': 'Максимум участников',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        location = cleaned_data.get('location')
        
        if start_datetime and end_datetime and location:
            # Проверяем, есть ли другое мероприятие в этом же месте в это же время
            conflicting_events = Event.objects.filter(
                location=location,
                status__in=['published', 'confirmed', 'in_progress'],
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime
            )
            if self.instance.pk:
                conflicting_events = conflicting_events.exclude(pk=self.instance.pk)
            
            if conflicting_events.exists():
                raise forms.ValidationError(
                    f'Помещение "{location}" уже занято в это время. '
                    f'Конфликт с мероприятием: {conflicting_events.first().title}'
                )
        
        return cleaned_data        

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

class InviteSpecialistForm(forms.Form):
    """Форма для приглашения специалиста"""
    specialist_id = forms.IntegerField(widget=forms.HiddenInput)
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Сообщение для специалиста...'}),
        required=False,
        label='Сообщение'
    )

