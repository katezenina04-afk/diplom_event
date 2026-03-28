from django.test import TestCase

from events.forms import EventForm


class EventFormValidationTests(TestCase):
    def test_end_datetime_must_not_be_before_start(self):
        form = EventForm(data={
            'title': 'Тест',
            'description': 'Описание',
            'start_datetime': '2026-04-01T12:00',
            'end_datetime': '2026-04-01T10:00',
            'location': 'Москва',
            'price': '500.00',
            'is_free': False,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('end_datetime', form.errors)

    def test_paid_event_requires_positive_price(self):
        form = EventForm(data={
            'title': 'Тест',
            'description': 'Описание',
            'start_datetime': '2026-04-01T12:00',
            'end_datetime': '2026-04-01T14:00',
            'location': 'Москва',
            'price': '0',
            'is_free': False,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)