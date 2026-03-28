from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('specialist', 'Специалист'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='user')

    phone = models.CharField('Телефон', max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class SpecialistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_profile',
        verbose_name='Пользователь',
    )
    full_name = models.CharField('ФИО', max_length=255)
    specialization = models.CharField('Специализация', max_length=255)
    competencies = models.TextField('Компетенции', blank=True)
    experience_years = models.PositiveIntegerField('Опыт (лет)', default=0)
    city = models.CharField('Город', max_length=120, blank=True)
    contact_email = models.EmailField('Контактный email', blank=True)
    is_verified = models.BooleanField('Проверен', default=False)
    moderation_status = models.CharField(
        'Статус модерации',
        max_length=20,
        choices=[('draft', 'Черновик'), ('pending', 'На проверке'), ('approved', 'Одобрен')],
        default='draft',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Профиль специалиста'
        verbose_name_plural = 'Профили специалистов'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.specialization})'
