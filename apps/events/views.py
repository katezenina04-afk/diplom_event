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
from .forms import EventForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import EventForm, CommentForm, ReviewForm


def event_list(request):
    """Афиша мероприятий с поиском, фильтрацией, сортировкой и пагинацией"""
    
    # Базовый запрос: только опубликованные и предстоящие
    events = Event.objects.filter(
        status='published',
        start_datetime__gte=timezone.now()
    )
    
    # ========== ПОИСК ==========
    q = request.GET.get('q', '')
    if q:
        events = events.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(location__icontains=q)
        )
    
    # ========== ФИЛЬТР ПО ДАТЕ ==========
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
    
    # ========== ФИЛЬТР ПО КАТЕГОРИИ ==========
    category_id = request.GET.get('category')
    if category_id:
        events = events.filter(category_id=category_id)
    
    # ========== СОРТИРОВКА ==========
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
    
    # ========== ПАГИНАЦИЯ ==========
    paginator = Paginator(events, 9)  # 9 мероприятий на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # ========== КОНТЕКСТ ==========
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
        events_by_day[day].append(event)
    
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
            event.status = 'published'
            event.save()
            form.save_m2m()
            messages.success(request, 'Мероприятие создано!')
            return redirect('event_detail', pk=event.id)
    else:
        form = EventForm()
    return render(request, 'events/create.html', {'form': form})


@login_required
def my_events(request):
    events = Event.objects.filter(creator=request.user).order_by('-start_datetime')
    return render(request, 'events/my_events.html', {'events': events})


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
    registration.delete()
    messages.success(request, f'Запись на "{event_title}" отменена')
    # Уведомление пользователю об отмене записи
    create_notification(
        user=request.user,
        notification_type='registration_cancelled',
        title='Запись отменена',
        message=f'Ваша запись на мероприятие "{event_title}" отменена',
        link=f'/events/{event.id}/'
    )
    return redirect('my_registrations')


@login_required
def recommendations(request):
    registered_events = Registration.objects.filter(user=request.user).values_list('event_id', flat=True)
    
    recommended = Event.objects.filter(
        status='published',
        start_datetime__gt=timezone.now()
    ).exclude(id__in=registered_events).order_by('start_datetime')[:10]
    
    return render(request, 'events/recommendations.html', {'recommendations': recommended})

@login_required
def add_comment(request, event_id):
    """Добавление комментария к мероприятию"""
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
    """Удаление комментария (только автор или администратор)"""
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
    """Поставить/убрать лайк (AJAX)"""
    event = get_object_or_404(Event, pk=event_id)
    like, created = Like.objects.get_or_create(event=event, user=request.user)
    
    if not created:
        # Если лайк уже был — удаляем
        like.delete()
        liked = False
    else:
        liked = True
    
    likes_count = event.likes.count()
    
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })

@login_required
def add_review(request, event_id):
    """Добавление отзыва о мероприятии"""
    event = get_object_or_404(Event, pk=event_id)
    
    # Проверяем, что пользователь был на мероприятии (статус attended)
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
        else:
            messages.error(request, 'Ошибка при сохранении отзыва')
    
    # Уведомление организатору о новом отзыве
    if review.event.creator != request.user:
        create_notification(
            user=review.event.creator,
            notification_type='new_review',
            title='Новый отзыв',
            message=f'{request.user.username} оставил отзыв на вашем мероприятии "{review.event.title}"',
            link=f'/events/{review.event.id}/'
        )

    return redirect('event_detail', pk=event_id)


@login_required
def delete_review(request, review_id):
    """Удаление отзыва"""
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
    """Добавить/удалить из избранного (AJAX)"""
    event = get_object_or_404(Event, pk=event_id)
    favorite, created = Favorite.objects.get_or_create(event=event, user=request.user)
    
    if not created:
        favorite.delete()
        favorited = False
    else:
        favorited = True
    
    favorites_count = event.favorites.count()
    
    return JsonResponse({
        'favorited': favorited,
        'favorites_count': favorites_count
    })


@login_required
def favorites_list(request):
    """Список избранных мероприятий"""
    favorites = Favorite.objects.filter(user=request.user).select_related('event')
    return render(request, 'events/favorites.html', {'favorites': favorites})

@login_required
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
    """Список уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Отмечаем все как прочитанные при просмотре
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'events/notifications.html', context)

@login_required
def event_statistics(request, pk):
    """Статистика мероприятия для организатора"""
    event = get_object_or_404(Event, pk=pk)
    
    # Проверяем, что пользователь — организатор
    if event.creator != request.user:
        messages.error(request, 'У вас нет доступа к статистике этого мероприятия')
        return redirect('event_detail', pk=pk)
    
    # Собираем статистику
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