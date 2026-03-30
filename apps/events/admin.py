from django.contrib import admin
from .models import Event, Category, Registration

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    fields = ('user', 'status', 'entry_code', 'created_at')
    readonly_fields = ('entry_code', 'created_at')
    can_delete = False

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'location', 'creator', 'status', 'get_participants_count')
    list_filter = ('status', 'start_datetime', 'categories')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_datetime'
    filter_horizontal = ('categories',)
    inlines = [RegistrationInline]
    fieldsets = (
        ('Основное', {'fields': ('title', 'description', 'image', 'creator', 'status')}),
        ('Время и место', {'fields': ('start_datetime', 'end_datetime', 'location')}),  # убрали latitude, longitude
        ('Категории и цена', {'fields': ('categories', 'price', 'is_free', 'max_participants')}),
    )
    
    def get_participants_count(self, obj):
        return obj.get_participants_count()
    get_participants_count.short_description = 'Участников'

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'entry_code', 'created_at')
    list_filter = ('status', 'event')
    search_fields = ('user__username', 'event__title')
    readonly_fields = ('entry_code', 'created_at')