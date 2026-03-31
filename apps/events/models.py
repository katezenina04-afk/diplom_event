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
        ('pending', 'На модерации'),
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
    views_count = models.PositiveIntegerField('Просмотры', default=0)
    
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
        ('pending', 'Ожидает подтверждения'),  # новый статус
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('attended', 'Посетил'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    entry_code = models.CharField('Код для входа', max_length=6, blank=True)
    
    is_invited = models.BooleanField('Приглашён организатором', default=False)  # новое поле
    
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
        return f"{self.user.username} → {self.event.title} ({self.get_status_display()})"

class Comment(models.Model):
    """Комментарий к мероприятию"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"


class Like(models.Model):
    """Лайк мероприятия"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ['event', 'user']  # один пользователь может лайкнуть мероприятие только один раз
    
    def __str__(self):
        return f"{self.user.username} → {self.event.title}"
    
class Review(models.Model):
    """Отзыв о мероприятии"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField('Оценка', choices=[(i, f'{i} звезд') for i in range(1, 6)])
    text = models.TextField('Текст отзыва', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ['event', 'user']  # один пользователь — один отзыв на мероприятие
    
    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.rating}★)"


class Favorite(models.Model):
    """Избранное мероприятие"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.username} → {self.event.title}"

class Notification(models.Model):
    """Уведомление для пользователя"""
    NOTIFICATION_TYPES = [
        ('new_event', 'Новое мероприятие'),
        ('new_comment', 'Новый комментарий'),
        ('new_review', 'Новый отзыв'),
        ('registration_confirmed', 'Запись подтверждена'),
        ('registration_cancelled', 'Запись отменена'),
        ('event_cancelled', 'Мероприятие отменено'),
        ('invitation', 'Приглашение на мероприятие'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField('Тип', max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField('Заголовок', max_length=200)
    message = models.TextField('Сообщение')
    link = models.CharField('Ссылка', max_length=200, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"