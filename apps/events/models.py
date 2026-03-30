from django.db import models
from django.conf import settings
import secrets

class Category(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField('Иконка', max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Афиша', upload_to='events/', blank=True, null=True)
    
    start_datetime = models.DateTimeField('Дата и время начала')
    end_datetime = models.DateTimeField('Дата и время окончания', blank=True, null=True)
    location = models.CharField('Место проведения', max_length=255)  # только адрес
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Категория'
    )
    
    price = models.DecimalField('Цена (руб)', max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField('Бесплатно', default=True)
    
    max_participants = models.PositiveIntegerField('Максимум участников', blank=True, null=True)
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name='Организатор'
    )
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['-start_datetime']
    
    def __str__(self):
        return self.title
    
    def get_participants_count(self):
        return self.registrations.filter(status='confirmed').count()
    
    def is_full(self):
        if self.max_participants:
            return self.get_participants_count() >= self.max_participants
        return False


class Registration(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('attended', 'Посетил'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    entry_code = models.CharField('Код для входа', max_length=6, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Регистрация'
        verbose_name_plural = 'Регистрации'
        unique_together = ['event', 'user']
    
    def save(self, *args, **kwargs):
        if not self.entry_code:
            self.entry_code = f"{secrets.randbelow(1000000):06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} → {self.event.title}"