from events.models import Notification
from events.models import Event

def unread_notifications(request):
    """Добавляет количество непрочитанных уведомлений в контекст"""
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {'unread_notifications_count': unread_count}

def pending_events_count(request):
    count = 0
    if request.user.is_authenticated and request.user.is_superuser:
        count = Event.objects.filter(status='pending').count()
    return {'pending_count': count}