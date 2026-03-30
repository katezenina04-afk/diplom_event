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