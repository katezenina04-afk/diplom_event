from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('specialists/', views.specialists_list_view, name='specialists_list'),
    path('specialists/<int:pk>/', views.specialist_detail_view, name='specialist_detail'),
    path('specialist/edit/', views.edit_specialist_profile_view, name='edit_specialist_profile'),
]
