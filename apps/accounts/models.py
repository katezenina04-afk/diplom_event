from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField('Роль', max_length=10, choices=ROLE_CHOICES, default='user')
    
    phone = models.CharField('Телефон', max_length=20, blank=True)
    # avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    # interests = models.ManyToManyField('events.Category', blank=True, verbose_name='Интересы')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username