from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from accounts.email_utils import send_reminder_email
from .models import Event

@shared_task
def send_event_reminders():
    """Отправка напоминаний за 24 часа до мероприятия"""
    from .models import Event, Registration
    
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    
    # Мероприятия, которые начнутся через 24 часа
    events = Event.objects.filter(
        start_datetime__date=tomorrow.date(),
        status='published'
    )
    
    for event in events:
        # Получаем всех участников
        registrations = Registration.objects.filter(
            event=event,
            status='confirmed'
        ).select_related('user')
        
        for reg in registrations:
            send_reminder_email(reg.user, event)

@shared_task
def update_expired_events_status():
    """Автоматическое обновление статуса мероприятий, дата которых прошла"""
    now = timezone.now()
    
    # Мероприятия со статусом "Опубликовано", у которых дата окончания прошла
    expired_events = Event.objects.filter(
        status='published',
        end_datetime__lt=now
    )
    
    count = expired_events.update(status='completed')
    
    if count > 0:
        print(f"Обновлено статусов мероприятий: {count}")
    
    return count