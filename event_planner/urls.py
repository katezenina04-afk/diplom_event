from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from events.models import Event, Category


def home_view(request):
    now = timezone.now()

    upcoming_events = Event.objects.filter(
        status='published',
        start_datetime__gte=now
    ).select_related('category', 'creator').order_by('start_datetime')[:6]

    popular_events = Event.objects.filter(
        status='published',
        start_datetime__gte=now
    ).select_related('category', 'creator').annotate(
        participants_total=Count('registrations')
    ).order_by('-participants_total', '-views_count', 'start_datetime')[:6]

    categories = Category.objects.all()[:8]

    stats = {
        'events_count': Event.objects.filter(status='published').count(),
        'categories_count': Category.objects.count(),
        'organizers_count': Event.objects.values('creator').distinct().count(),
    }

    context = {
        'upcoming_events': upcoming_events,
        'popular_events': popular_events,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'index.html', context)


urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('events/', include('events.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)