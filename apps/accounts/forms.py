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


# НОВАЯ ФОРМА ДЛЯ РЕДАКТИРОВАНИЯ ПРОФИЛЯ
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Электронная почта',
            'phone': 'Телефон',
        }