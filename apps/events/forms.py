from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'image',
            'start_datetime', 'end_datetime', 'location',
            'latitude', 'longitude',
            'categories', 'price', 'is_free', 'max_participants'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
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
            'latitude': 'Широта',
            'longitude': 'Долгота',
            'categories': 'Категории',
            'price': 'Цена (руб)',
            'is_free': 'Бесплатное мероприятие',
            'max_participants': 'Максимум участников',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        is_free = cleaned_data.get('is_free')
        price = cleaned_data.get('price')

        if start_datetime and end_datetime and end_datetime < start_datetime:
            self.add_error('end_datetime', 'Дата окончания не может быть раньше даты начала.')

        if is_free:
            cleaned_data['price'] = 0
        elif price is None or price <= 0:
            self.add_error('price', 'Для платного мероприятия укажите цену больше 0.')

        return cleaned_data