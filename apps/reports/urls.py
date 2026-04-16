from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('organizers/', views.organizer_report, name='organizer_report'),
    path('events/', views.events_report, name='events_report'),
    path('participants/', views.participants_report, name='participants_report'),
    path('export/events/', views.export_events_excel, name='export_events_excel'),
    path('export/specialists/', views.export_specialists_excel, name='export_specialists_excel'),
    path('export/organizers/', views.export_organizers_excel, name='export_organizers_excel'),
]