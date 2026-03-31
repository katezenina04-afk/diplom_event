from events.models import Notification

def unread_notifications(request):
    """Добавляет количество непрочитанных уведомлений в контекст"""
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {'unread_notifications_count': unread_count}