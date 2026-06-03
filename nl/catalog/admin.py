from django.contrib import admin
from .models import Category, Request, Comment, RequestHistory, UserProfile, UserRole

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    prepopulated_fields = {'name': ['name']}

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'status', 'priority', 'executor', 'created_date']
    list_filter = ['status', 'priority', 'category', 'created_date']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_date', 'updated_date']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority', 'executor')
        }),
        ('Сроки', {
            'fields': ('deadline', 'created_date', 'updated_date')
        }),
        ('Внутренние заметки', {
            'fields': ('internal_notes',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'author', 'created_date']
    list_filter = ['created_date', 'author']
    search_fields = ['text', 'author__username', 'request__title']

@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'changed_by', 'changed_field', 'change_date']
    list_filter = ['changed_field', 'change_date']
    search_fields = ['request__title', 'changed_by__username']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_requests']
    search_fields = ['user__username']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role']
    list_filter = ['role']
    search_fields = ['user__username']