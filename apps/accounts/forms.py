from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import SpecialistProfile, User


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


class SpecialistProfileForm(forms.ModelForm):
    class Meta:
        model = SpecialistProfile
        fields = [
            'full_name',
            'specialization',
            'competencies',
            'experience_years',
            'city',
            'contact_email',
            'moderation_status',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'competencies': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'moderation_status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'full_name': 'ФИО',
            'specialization': 'Специализация',
            'competencies': 'Компетенции',
            'experience_years': 'Опыт (лет)',
            'city': 'Город',
            'contact_email': 'Контактный email',
            'moderation_status': 'Статус модерации',
        }
