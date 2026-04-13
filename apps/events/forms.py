from django import forms
from django.db import models
from django.conf import settings
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

class Assignment(models.Model):
    """Назначение специалиста на мероприятие"""
    ROLE_CHOICES = [
        ('host', 'Ведущий'),
        ('speaker', 'Докладчик'),
        ('assistant', 'Ассистент'),
        ('participant', 'Участник'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждён'),
        ('rejected', 'Отклонён'),
    ]
    
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='assignments')
    specialist = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='assignments')
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='participant')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField('Сообщение', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'
        unique_together = ['event', 'specialist']
    
    def __str__(self):
        return f"{self.specialist.username} → {self.event.title} ({self.get_role_display()})"