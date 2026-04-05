from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import models
import calendar
from .models import Event, Category, Registration, Comment, Like, Review, Favorite, Notification
from .forms import EventForm, CommentForm, ReviewForm
from django.http import JsonResponse
from accounts.models import User
from .recommender import generate_recommendations
from django.contrib.admin.views.decorators import staff_member_required
from accounts.email_utils import (
    send_event_registration_email,
    send_moderation_result_email,
    send_invitation_email,
    send_reminder_email
)

def event_list(request):
    """Афиша мероприятий с поиском, фильтрацией, сортировкой и пагинацией"""
    
    events = Event.objects.filter(
        status='published',
        start_datetime__gte=timezone.now()
    )
    
    q = request.GET.get('q', '')
    if q:
        events = events.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(location__icontains=q)
        )
    
    date_filter = request.GET.get('date', '')
    today = timezone.now().date()
    
    if date_filter == 'today':
        events = events.filter(start_datetime__date=today)
    elif date_filter == 'tomorrow':
        events = events.filter(start_datetime__date=today + timedelta(days=1))
    elif date_filter == 'week':
        next_week = today + timedelta(days=7)
        events = events.filter(start_datetime__date__range=[today, next_week])
    elif date_filter == 'month':
        next_month = today + timedelta(days=30)
        events = events.filter(start_datetime__date__range=[today, next_month])
    
    category_id = request.GET.get('category')
    if category_id:
        events = events.filter(category_id=category_id)
    
    sort = request.GET.get('sort', 'date_asc')
    
    if sort == 'date_asc':
        events = events.order_by('start_datetime')
    elif sort == 'date_desc':
        events = events.order_by('-start_datetime')
    elif sort == 'price_asc':
        events = events.order_by('price')
    elif sort == 'price_desc':
        events = events.order_by('-price')
    elif sort == 'popular':
        events = events.annotate(participants_count=Count('registrations')).order_by('-participants_count')
    
    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'events': page_obj,
        'categories': categories,
        'q': q,
        'date_filter': date_filter,
        'selected_category': int(category_id) if category_id else None,
        'sort': sort,
        'page_obj': page_obj,
    }
    return render(request, 'events/list.html', context)

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    is_registered = False
    registration = None
    user_liked = False
    user_favorited = False
    user_registered = False
    user_registered_attended = False
    event.views_count += 1
    event.save(update_fields=['views_count'])
    
    # <<<<< ДОБАВЛЕНО: проверка, прошло ли мероприятие
    is_past = False
    if event.end_datetime:
        is_past = event.end_datetime < timezone.now()
    else:
        is_past = event.start_datetime < timezone.now()
    # >>>>> КОНЕЦ ДОБАВЛЕНИЯ
    
    if request.user.is_authenticated:
        registration = Registration.objects.filter(event=event, user=request.user).first()
        is_registered = registration is not None
        user_registered = registration is not None
        user_registered_attended = registration is not None and registration.status == 'attended'
        user_liked = Like.objects.filter(event=event, user=request.user).exists()
        user_favorited = Favorite.objects.filter(event=event, user=request.user).exists()
    
    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'user_registered': user_registered,
        'user_registered_attended': user_registered_attended,
        'is_past': is_past,  # <<<<< ДОБАВЛЕНО
    }
    return render(request, 'events/detail.html', context)


def event_calendar(request, year=None, month=None):
    if not year:
        year = timezone.now().year
    if not month:
        month = timezone.now().month
    
    year = int(year)
    month = int(month)
    
    first_day = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    
    events = Event.objects.filter(
        start_datetime__year=year,
        start_datetime__month=month,
        status='published'
    ).order_by('start_datetime')
    
    events_by_day = {}
    for event in events:
        day = event.start_datetime.day
        if day not in events_by_day:
            events_by_day[day] = []
        
        # <<<<< ИЗМЕНЕНО: добавляем информацию о том, прошло ли мероприятие
        is_past = False
        if event.end_datetime:
            is_past = event.end_datetime < timezone.now()
        else:
            is_past = event.start_datetime < timezone.now()
        # >>>>> КОНЕЦ ИЗМЕНЕНИЙ
        
        events_by_day[day].append({
            'event': event,
            'is_past': is_past,  # <<<<< ДОБАВЛЕНО
        })
    
    calendar_data = []
    week = []
    first_weekday = first_day.weekday()
    
    for _ in range(first_weekday):
        week.append({'day': None, 'events': []})
    
    for day in range(1, last_day + 1):
        week.append({
            'day': day,
            'events': events_by_day.get(day, []),
            'is_today': (year == timezone.now().year and month == timezone.now().month and day == timezone.now().day)
        })
        if len(week) == 7:
            calendar_data.append(week)
            week = []
    
    if week:
        while len(week) < 7:
            week.append({'day': None, 'events': []})
        calendar_data.append(week)
    
    month_names = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
                   5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
                   9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1
    
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year = year + 1
    
    context = {
        'calendar_data': calendar_data,
        'month_name': month_names[month],
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    return render(request, 'events/calendar.html', context)


@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.status = 'pending'  # теперь не сразу публикуется, а на модерацию
            event.save()
            form.save_m2m()
            
            # Уведомление администратору
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                create_notification(
                    user=admin,
                    notification_type='event_pending',
                    title='Новая заявка на мероприятие',
                    message=f'{request.user.username} создал мероприятие "{event.title}" и ожидает модерации',
                    link=f'/events/moderate/{event.id}/'
                )
            
            messages.success(request, 'Мероприятие отправлено на модерацию. Ожидайте решения администратора.')
            return redirect('my_events')
    else:
        form = EventForm()
    return render(request, 'events/create.html', {'form': form})


@login_required
def my_events(request):
    """Мои мероприятия с фильтром по статусу"""
    tab = request.GET.get('tab', 'draft')
    
    if tab == 'draft':
        events = Event.objects.filter(creator=request.user, status='draft')
    elif tab == 'pending':
        events = Event.objects.filter(creator=request.user, status='pending')
    elif tab == 'published':
        events = Event.objects.filter(creator=request.user, status='published')
    elif tab == 'rejected':
        events = Event.objects.filter(creator=request.user, status='rejected')
    else:
        events = Event.objects.filter(creator=request.user)
    
    context = {
        'events': events.order_by('-created_at'),
        'active_tab': tab,
    }
    return render(request, 'events/my_events.html', context)


@login_required
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk, creator=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Мероприятие обновлено')
            return redirect('event_detail', pk=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/edit.html', {'form': form, 'event': event})


@login_required
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk, creator=request.user)
    event.delete()
    messages.success(request, 'Мероприятие удалено')
    return redirect('my_events')


@login_required
def my_registrations(request):
    registrations = Registration.objects.filter(user=request.user).select_related('event').order_by('-created_at')
    return render(request, 'events/my_registrations.html', {'registrations': registrations})


@login_required
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if event.status != 'published':
        messages.error(request, 'Мероприятие недоступно для записи')
        return redirect('event_detail', pk=pk)
    
    if Registration.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, 'Вы уже записаны на это мероприятие')
        return redirect('event_detail', pk=pk)
    
    if event.is_full():
        messages.error(request, 'Все места заняты')
        return redirect('event_detail', pk=pk)
    
    reg = Registration.objects.create(event=event, user=request.user, status='confirmed')
    messages.success(request, f'Вы успешно записаны! Ваш код для входа: {reg.entry_code}')
    
    # Отправка email-уведомления
    send_event_registration_email(request.user, event)

    create_notification(
        user=request.user,
        notification_type='registration_confirmed',
        title='Вы записаны на мероприятие',
        message=f'Вы успешно записались на мероприятие "{event.title}". Ваш код для входа: {reg.entry_code}',
        link=f'/events/{event.id}/'
    )
    return redirect('event_detail', pk=pk)


@login_required
def cancel_registration(request, pk):
    registration = get_object_or_404(Registration, pk=pk, user=request.user)
    event_title = registration.event.title
    event_id = registration.event.id
    registration.delete()
    messages.success(request, f'Запись на "{event_title}" отменена')
    
    create_notification(
        user=request.user,
        notification_type='registration_cancelled',
        title='Запись отменена',
        message=f'Ваша запись на мероприятие "{event_title}" отменена',
        link=f'/events/{event_id}/'
    )
    return redirect('my_registrations')


@login_required
def recommendations(request):
    """ML-рекомендации для специалиста"""
    
    registered_events = Registration.objects.filter(user=request.user).values_list('event_id', flat=True)
    
    # Проверяем, заполнен ли профиль
    has_profile_data = bool(request.user.skills or request.user.experience or request.user.specialization.exists())
    
    if not has_profile_data or request.user.role == 'admin':
        # Обычные рекомендации (просто последние мероприятия)
        recommended_events = Event.objects.filter(
            status='published',
            start_datetime__gt=timezone.now()
        ).exclude(id__in=registered_events).order_by('start_datetime')[:10]
        
        # Преобразуем в формат, совместимый с шаблоном
        recommendations = []
        for event in recommended_events:
            recommendations.append({
                'event': event,
                'score': 0,
                'percent_score': 0,
                'reasons': []
            })
        is_ml = False
    else:
        # ML-рекомендации
        recommendations = generate_recommendations(request.user, limit=10)
        is_ml = True
    
    context = {
        'recommendations': recommendations,
        'is_ml': is_ml,
    }
    return render(request, 'events/recommendations.html', context)


@login_required
def add_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
            
            # Уведомление организатору о новом комментарии
            if comment.event.creator != request.user:
                create_notification(
                    user=comment.event.creator,
                    notification_type='new_comment',
                    title='Новый комментарий',
                    message=f'{request.user.username} оставил комментарий на вашем мероприятии "{comment.event.title}"',
                    link=f'/events/{comment.event.id}/'
                )
    
    return redirect('event_detail', pk=event_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if request.user == comment.user or request.user.is_superuser:
        event_id = comment.event.id
        comment.delete()
        messages.success(request, 'Комментарий удалён')
    else:
        messages.error(request, 'У вас нет прав на удаление этого комментария')
    
    return redirect('event_detail', pk=event_id)


@login_required
def toggle_like(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    like, created = Like.objects.get_or_create(event=event, user=request.user)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': event.likes.count()
    })

@login_required
def add_review(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    registration = Registration.objects.filter(
        event=event, 
        user=request.user, 
        status='attended'
    ).exists()
    
    if not registration:
        messages.error(request, 'Вы можете оставить отзыв только после посещения мероприятия')
        return redirect('event_detail', pk=event_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.user = request.user
            review.save()
            messages.success(request, 'Спасибо за отзыв!')
            
            # Уведомление организатору о новом отзыве
            if review.event.creator != request.user:
                create_notification(
                    user=review.event.creator,
                    notification_type='new_review',
                    title='Новый отзыв',
                    message=f'{request.user.username} оставил отзыв на вашем мероприятии "{review.event.title}"',
                    link=f'/events/{review.event.id}/'
                )
        else:
            messages.error(request, 'Ошибка при сохранении отзыва')
    
    return redirect('event_detail', pk=event_id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    
    if request.user == review.user or request.user.is_superuser:
        event_id = review.event.id
        review.delete()
        messages.success(request, 'Отзыв удалён')
    else:
        messages.error(request, 'У вас нет прав на удаление этого отзыва')
    
    return redirect('event_detail', pk=event_id)


@login_required
def toggle_favorite(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    favorite, created = Favorite.objects.get_or_create(event=event, user=request.user)
    
    if not created:
        favorite.delete()
        favorited = False
    else:
        favorited = True
    
    return JsonResponse({
        'favorited': favorited,
        'favorites_count': event.favorites.count()
    })


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('event')
    return render(request, 'events/favorites.html', {'favorites': favorites})


def create_notification(user, notification_type, title, message, link=''):
    """Создание уведомления"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'events/notifications.html', context)


@login_required
def event_statistics(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    if event.creator != request.user:
        messages.error(request, 'У вас нет доступа к статистике этого мероприятия')
        return redirect('event_detail', pk=pk)
    
    stats = {
        'views': event.views_count,
        'registrations': event.registrations.count(),
        'confirmed_registrations': event.registrations.filter(status='confirmed').count(),
        'attended': event.registrations.filter(status='attended').count(),
        'favorites': event.favorites.count(),
        'likes': event.likes.count(),
        'comments': event.comments.count(),
        'reviews': event.reviews.count(),
        'average_rating': event.reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0,
    }
    
    context = {
        'event': event,
        'stats': stats,
    }
    return render(request, 'events/statistics.html', context)

def search_specialists(request, event_id):
    """Поиск специалистов для приглашения на мероприятие"""
    event = get_object_or_404(Event, pk=event_id, creator=request.user)
    
    # Поиск по навыкам и опыту
    query = request.GET.get('q', '')
    
    specialists = User.objects.filter(
        looking_for_work=True,
        role='user'  # обычные пользователи, не админы
    ).exclude(id=request.user.id)  # исключаем себя
    
    if query:
        specialists = specialists.filter(
            Q(skills__icontains=query) |
            Q(experience__icontains=query)
        ).distinct()
    
    # Ранжируем по релевантности
    specialists = specialists.annotate(
        relevance = (
            models.Case(
                models.When(skills__icontains=query, then=models.Value(10)),
                models.When(experience__icontains=query, then=models.Value(5)),
                default=models.Value(0),
                output_field=models.IntegerField()
            )
        )
    ).order_by('-relevance')
    
    context = {
        'event': event,
        'specialists': specialists,
        'query': query,
    }
    return render(request, 'events/invite_specialists.html', context)


@login_required
def invite_specialist(request, event_id, specialist_id):
    """Пригласить специалиста на мероприятие"""
    event = get_object_or_404(Event, pk=event_id, creator=request.user)
    specialist = get_object_or_404(User, pk=specialist_id)
    
    # Проверяем, что специалист ищет работу
    if not specialist.looking_for_work:
        messages.warning(request, f'{specialist.username} не ищет работу')
        return redirect('search_specialists', event_id=event.id)
    
    # Проверяем, не записан ли уже
    existing = Registration.objects.filter(event=event, user=specialist).first()
    if existing:
        if existing.status == 'confirmed':
            messages.warning(request, f'{specialist.username} уже записан на это мероприятие')
        elif existing.status == 'pending':
            messages.warning(request, f'{specialist.username} уже приглашён')
        return redirect('search_specialists', event_id=event.id)
    
    # Создаём запись в статусе pending (ожидает подтверждения)
    registration = Registration.objects.create(
        event=event,
        user=specialist,
        status='pending',
        is_invited=True
    )
    
    # Получаем сообщение
    message = request.GET.get('message', '') or request.POST.get('message', '')
    
    # Создаём уведомление
    create_notification(
    user=specialist,
    notification_type='invitation',
    title=f'Приглашение на мероприятие "{event.title}"',
    message=f'{request.user.username} приглашает вас на мероприятие "{event.title}".\n\n{message}' if message else f'{request.user.username} приглашает вас на мероприятие "{event.title}".',
    link=f'/events/accept-invitation/{registration.id}/'  # вот так
)
    
    messages.success(request, f'Приглашение отправлено пользователю {specialist.username}')
    # Отправка email-уведомления специалисту
    send_invitation_email(specialist, event, message)
    return redirect('edit_event', pk=event.id)

@login_required
def accept_invitation(request, registration_id):
    """Принять приглашение на мероприятие"""
    print(f"DEBUG: accept_invitation called with registration_id={registration_id}")
    registration = get_object_or_404(Registration, pk=registration_id, user=request.user, status='pending')
    print(f"DEBUG: registration found: {registration}")
    
    # Меняем статус на confirmed
    registration.status = 'confirmed'
    registration.save()
    
    messages.success(request, f'Вы приняли приглашение на мероприятие "{registration.event.title}"! Ваш код для входа: {registration.entry_code}')
    
    return redirect('event_detail', pk=registration.event.id)

def events_map(request):
    """Карта всех мероприятий"""
    events = Event.objects.filter(status='published')
    
    # Преобразуем QuerySet в список словарей для JSON
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'location': event.location,
            'start_datetime': event.start_datetime.strftime('%d.%m.%Y %H:%M'),
            'url': f'/events/{event.id}/',
        })
    
    return render(request, 'events/map.html', {'events_data': events_data})

@staff_member_required
def moderate_event(request, event_id):
    """Страница модерации мероприятия"""
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            event.status = 'published'
            event.moderation_comment = ''
            event.save()
            
            # Уведомление организатору в системе
            create_notification(
                user=event.creator,
                notification_type='event_approved',
                title='Ваше мероприятие одобрено',
                message=f'Ваше мероприятие "{event.title}" успешно опубликовано.',
                link=f'/events/{event.id}/'
            )
            
            # Отправка email-уведомления организатору
            send_moderation_result_email(event.creator, event, 'approved')
            
            messages.success(request, 'Мероприятие одобрено и опубликовано')
            
        elif action == 'reject':
            event.status = 'rejected'
            event.moderation_comment = comment
            event.save()
            
            # Уведомление организатору в системе
            create_notification(
                user=event.creator,
                notification_type='event_rejected',
                title='Ваше мероприятие отклонено',
                message=f'Ваше мероприятие "{event.title}" отклонено.\n\nПричина: {comment}' if comment else f'Ваше мероприятие "{event.title}" отклонено.',
                link=f'/events/{event.id}/'
            )
            
            # Отправка email-уведомления организатору
            send_moderation_result_email(event.creator, event, 'rejected', comment)
            
            messages.success(request, 'Мероприятие отклонено')
        
        return redirect('pending_events')
    
    context = {
        'event': event,
    }
    return render(request, 'events/moderate.html', context)


@staff_member_required
def pending_events(request):
    """Список заявок на модерацию"""
    events = Event.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'events/pending_events.html', {'events': events})