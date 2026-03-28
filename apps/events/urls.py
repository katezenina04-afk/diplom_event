from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('calendar/', views.event_calendar, name='event_calendar'),
    path('calendar/<int:year>/<int:month>/', views.event_calendar, name='event_calendar'),
    
    path('create/', views.create_event, name='create_event'),
    path('my-events/', views.my_events, name='my_events'),
    path('edit/<int:pk>/', views.edit_event, name='edit_event'),
    path('delete/<int:pk>/', views.delete_event, name='delete_event'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('register/<int:pk>/', views.register_for_event, name='register_for_event'),
    path('cancel/<int:pk>/', views.cancel_registration, name='cancel_registration'),
    path('recommendations/', views.recommendations, name='recommendations'),
]