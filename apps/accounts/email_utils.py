from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email_notification(user, subject, message, html_template=None, context=None):
    """Отправка email-уведомления пользователю"""
    if not user.email: 
        return
    
    if html_template and context:
        html_message = render_to_string(html_template, context)
        plain_message = strip_tags(html_message)
    else:
        html_message = None
        plain_message = message   
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_registration_email(user):
    """Отправка приветственного письма при регистрации"""
    subject = 'Добро пожаловать в Event Planner!'
    message = f"""
    Здравствуйте, {user.username}!
    
    Вы успешно зарегистрировались в системе Event Planner.
    
    Теперь вы можете:
    - Создавать и публиковать мероприятия
    - Записываться на интересующие вас события
    - Получать персонализированные рекомендации
    
    С уважением,
    Команда Event Planner
    """
    send_email_notification(user, subject, message)


def send_event_registration_email(user, event):
    """Отправка письма при записи на мероприятие"""
    subject = f'Вы записаны на мероприятие "{event.title}"'
    context = {
        'user': user,
        'event': event,
        'entry_code': None,
    }
    
    # Получаем код для входа
    from events.models import Registration
    reg = Registration.objects.filter(event=event, user=user).first()
    if reg:
        context['entry_code'] = reg.entry_code
    
    send_email_notification(
        user, subject, '',
        html_template='emails/event_registration.html',
        context=context
    )


def send_moderation_result_email(user, event, status, comment=''):
    """Отправка письма о результате модерации"""
    if status == 'approved':
        subject = f'Ваше мероприятие "{event.title}" одобрено!'
        message = f"""
        Здравствуйте, {user.username}!
        
        Ваше мероприятие "{event.title}" прошло модерацию и опубликовано на сайте.
        
        Теперь пользователи могут записываться на него.
        
        Ссылка на мероприятие: http://127.0.0.1:8000/events/{event.id}/
        
        С уважением,
        Команда Event Planner
        """
    else:
        subject = f'Ваше мероприятие "{event.title}" отклонено'
        message = f"""
        Здравствийте, {user.username}!
        
        Ваше мероприятие "{event.title}" отклонено по следующей причине:
        
        {comment}
        
        Пожалуйста, исправьте указанные замечания и отправьте мероприятие на повторную модерацию.
        
        С уважением,
        Команда Event Planner
        """
    
    send_email_notification(user, subject, message)


def send_invitation_email(specialist, event, message=''):
    """Отправка письма о приглашении на мероприятие"""
    subject = f'Приглашение на мероприятие "{event.title}"'
    email_message = f"""
    Здравствуйте, {specialist.username}!
    
    {event.creator.username} приглашает вас принять участие в мероприятии "{event.title}".
    
    Детали мероприятия:
    - Дата: {event.start_datetime.strftime('%d.%m.%Y %H:%M')}
    - Место: {event.location}
    
    {message}
    
    Подробнее: http://127.0.0.1:8000/events/{event.id}/
    
    С уважением,
    Команда Event Planner
    """
    send_email_notification(specialist, subject, email_message)


def send_reminder_email(user, event):
    """Отправка напоминания за 24 часа до мероприятия"""
    subject = f'Напоминание: мероприятие "{event.title}" завтра!'
    context = {
        'user': user,
        'event': event,
    }
    send_email_notification(
        user, subject, '',
        html_template='emails/event_reminder.html',
        context=context
    )