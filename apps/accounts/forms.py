from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Электронная почта')
    phone = forms.CharField(required=False, label='Телефон')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone')
        labels = {
            'username': 'Имя пользователя',
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = 'user'
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'skills', 'experience', 'portfolio', 'looking_for_work')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Ведите, ассистент, работа с залом...'}),
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Опишите ваш опыт...'}),
            'portfolio': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'looking_for_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Электронная почта',
            'phone': 'Телефон',
            'skills': 'Навыки',
            'experience': 'Опыт работы',
            'portfolio': 'Портфолио (ссылка)',
            'looking_for_work': 'Ищу работу',
        }
        help_texts = {
            'skills': 'Перечислите ваши ключевые навыки',
            'experience': 'Опишите ваш опыт работы на мероприятиях',
            'portfolio': 'Ссылка на видео или сайт с примерами работ',
        }