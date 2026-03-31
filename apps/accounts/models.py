from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField('Роль', max_length=10, choices=ROLE_CHOICES, default='user')
    
    phone = models.CharField('Телефон', max_length=20, blank=True)
    
    # Дополнительные поля для специалиста
    skills = models.TextField('Навыки', blank=True, help_text='Например: "Ведение мероприятий, работа с аудиторией, MS Office"')
    experience = models.TextField('Опыт работы', blank=True, help_text='Опишите ваш опыт работы на мероприятиях')
    portfolio = models.URLField('Портфолио', blank=True, help_text='Ссылка на видео/сайт с примерами работ')
    looking_for_work = models.BooleanField('Ищу работу', default=False, help_text='Отметьте, если вы открыты для предложений')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username