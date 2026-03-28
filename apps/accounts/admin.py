from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SpecialistProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'user', 'is_verified', 'moderation_status')
    list_filter = ('is_verified', 'moderation_status', 'specialization')
    search_fields = ('full_name', 'specialization', 'user__username')