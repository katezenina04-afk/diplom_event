from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date
import calendar
from .models import Event, Category, Registration
from .forms import EventForm


def event_list(request):
    events = Event.objects.filter(
        status='published',
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')
    categories = Category.objects.all()
    context = {'events': events, 'categories': categories}
    return render(request, 'events/list.html', context)


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    is_registered = False
    registration = None
    if request.user.is_authenticated:
        registration = Registration.objects.filter(event=event, user=request.user).first()
        is_registered = registration is not None
    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
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
    return redirect('event_detail', pk=pk)


@login_required
def cancel_registration(request, pk):
    registration = get_object_or_404(Registration, pk=pk, user=request.user)
    event_title = registration.event.title
    registration.delete()
    messages.success(request, f'Запись на "{event_title}" отменена')
    return redirect('my_registrations')


@login_required
def recommendations(request):
    registered_events = Registration.objects.filter(user=request.user).values_list('event_id', flat=True)
    
    recommended = Event.objects.filter(
        status='published',
        start_datetime__gt=timezone.now()
    ).exclude(id__in=registered_events).order_by('start_datetime')[:10]
    
    return render(request, 'events/recommendations.html', {'recommendations': recommended})