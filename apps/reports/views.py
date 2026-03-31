from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.db.models import Count, Sum, Avg
from events.models import Event, Registration, Comment, Like, Favorite, Review
from accounts.models import User
from datetime import datetime
import pandas as pd
from io import BytesIO
from django.db import models

@staff_member_required
def reports_dashboard(request):
    """Главная страница отчётов"""
    return render(request, 'reports/dashboard.html')


@staff_member_required
def specialist_report(request):
    """Отчёт по специалистам (организаторам)"""
    # Специалисты — пользователи, которые создали хотя бы одно мероприятие
    specialists = User.objects.filter(created_events__isnull=False).distinct()
    
    data = []
    for user in specialists:
        events_count = user.created_events.count()
        total_participants = Registration.objects.filter(event__creator=user).count()
        total_likes = Like.objects.filter(event__creator=user).count()
        total_favorites = Favorite.objects.filter(event__creator=user).count()
        total_comments = Comment.objects.filter(event__creator=user).count()
        avg_rating = Review.objects.filter(event__creator=user).aggregate(avg=models.Avg('rating'))['avg'] or 0
        
        data.append({
            'user': user,
            'events_count': events_count,
            'total_participants': total_participants,
            'total_likes': total_likes,
            'total_favorites': total_favorites,
            'total_comments': total_comments,
            'avg_rating': round(avg_rating, 1),
        })
    
    # Сортируем по количеству мероприятий
    data.sort(key=lambda x: x['events_count'], reverse=True)
    
    context = {
        'data': data,
        'total_specialists': len(data),
        'total_events': Event.objects.count(),
        'total_participants': Registration.objects.count(),
    }
    return render(request, 'reports/specialist_report.html', context)


@staff_member_required
def events_report(request):
    """Отчёт по мероприятиям"""
    events = Event.objects.all().order_by('-created_at')
    
    data = []
    for event in events:
        data.append({
            'event': event,
            'participants': event.registrations.count(),
            'likes': event.likes.count(),
            'favorites': event.favorites.count(),
            'comments': event.comments.count(),
            'avg_rating': event.reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0,
        })
    
    # Статистика по статусам с процентами
    total_events = events.count()
    status_stats = {}
    for status_code, status_name in Event.STATUS_CHOICES:
        count = Event.objects.filter(status=status_code).count()
        percent = (count / total_events * 100) if total_events > 0 else 0
        status_stats[status_name] = {'count': count, 'percent': round(percent, 1)}
    
    # Статистика по месяцам с процентами
    from django.db.models.functions import TruncMonth
    monthly_stats = Event.objects.filter(status='published').annotate(
        month=TruncMonth('start_datetime')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Для месячной статистики считаем проценты
    total_monthly = sum(item['count'] for item in monthly_stats)
    monthly_data = []
    for item in monthly_stats:
        percent = (item['count'] / total_monthly * 100) if total_monthly > 0 else 0
        monthly_data.append({
            'month': item['month'],
            'count': item['count'],
            'percent': round(percent, 1)
        })
    
    context = {
        'data': data,
        'status_stats': status_stats,
        'monthly_stats': monthly_data,
        'total_events': total_events,
    }
    return render(request, 'reports/events_report.html', context)


@staff_member_required
def participants_report(request):
    """Отчёт по участникам"""
    participants = User.objects.filter(event_registrations__isnull=True).distinct()
    
    data = []
    for user in participants:
        registrations_count = user.event_registrations.count()
        events_attended = user.event_registrations.filter(status='attended').count()
        
        # Получаем категории мероприятий, которые посещал
        categories = []
        for reg in user.event_registrations.all():
            if reg.event.category:
                categories.append(reg.event.category.name)
        
        from collections import Counter
        top_categories = Counter(categories).most_common(3)
        
        data.append({
            'user': user,
            'registrations_count': registrations_count,
            'events_attended': events_attended,
            'top_categories': top_categories,
            'has_restrictions': user.dietary_restrictions.exists() if hasattr(user, 'dietary_restrictions') else False,
        })
    
    data.sort(key=lambda x: x['registrations_count'], reverse=True)
    
    context = {
        'data': data,
        'total_participants': participants.count(),
        'total_registrations': Registration.objects.count(),
    }
    return render(request, 'reports/participants_report.html', context)


@staff_member_required
def export_events_excel(request):
    """Экспорт мероприятий в Excel"""
    events = Event.objects.all().order_by('-start_datetime')
    
    # Создаём DataFrame
    df = pd.DataFrame([{
        'ID': e.id,
        'Название': e.title,
        'Дата начала': e.start_datetime.strftime('%d.%m.%Y %H:%M'),
        'Дата окончания': e.end_datetime.strftime('%d.%m.%Y %H:%M') if e.end_datetime else '',
        'Место': e.location,
        'Категория': e.category.name if e.category else '',
        'Цена': e.price if not e.is_free else 'Бесплатно',
        'Участников': e.registrations.count(),
        'Лайков': e.likes.count(),
        'Избранное': e.favorites.count(),
        'Комментариев': e.comments.count(),
        'Средний рейтинг': round(e.reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0, 1),
        'Статус': e.get_status_display(),
        'Организатор': e.creator.username,
    } for e in events])
    
    # Создаём Excel файл
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Мероприятия', index=False)
        
        # Настраиваем ширину колонок
        worksheet = writer.sheets['Мероприятия']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=events_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return response


@staff_member_required
def export_specialists_excel(request):
    """Экспорт специалистов в Excel"""
    specialists = User.objects.filter(created_events__isnull=False).distinct()
    
    df = pd.DataFrame([{
        'ID': u.id,
        'Имя пользователя': u.username,
        'Email': u.email,
        'Телефон': u.phone or '',
        'Мероприятий': u.created_events.count(),
        'Участников': Registration.objects.filter(event__creator=u).count(),
        'Лайков': Like.objects.filter(event__creator=u).count(),
        'Избранное': Favorite.objects.filter(event__creator=u).count(),
        'Средний рейтинг': round(Review.objects.filter(event__creator=u).aggregate(avg=models.Avg('rating'))['avg'] or 0, 1),
        'Навыки': u.skills or '',
        'Опыт': u.experience or '',
        'Дата регистрации': u.date_joined.strftime('%d.%m.%Y'),
    } for u in specialists])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Специалисты', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=specialists_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return response