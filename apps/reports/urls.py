from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('specialists/', views.specialist_report, name='specialist_report'),
    path('events/', views.events_report, name='events_report'),
    path('participants/', views.participants_report, name='participants_report'),
    path('export/events/', views.export_events_excel, name='export_events_excel'),
    path('export/specialists/', views.export_specialists_excel, name='export_specialists_excel'),
]