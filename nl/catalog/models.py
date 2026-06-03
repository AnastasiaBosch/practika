from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

class Category(models.Model):
    #name = models.CharField(max_length=200, help_text="Укажите жанр книги (например, научная фантастика, французская поэзия и т.д.)")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_requests = models.PositiveIntegerField(default=0, verbose_name="Всего заявок")
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
class Request(models.Model):
    STATUS_CHOICES = [
        ('new', '🟡 Создан'),
        ('in_progress', '🔵 В работе'),
        ('completed', '🟢 Выполнена'),
        ('rejected', '🔴 Отклонена'),
    ]

    PRIORITY_CHOICES = [
        ('low', '🟢 Низкий'),
        ('medium', '🟡 Средний'),
        ('high', '🔴 Высокий'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests', verbose_name="Автор")
    title = models.CharField(max_length=200, verbose_name="Тема заявки")
    description = models.TextField(verbose_name="Описание проблемы/задачи")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    executor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_requests',
        verbose_name="Исполнитель"
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет"
    )
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")

    # Внутренние заметки (только для менеджеров)
    internal_notes = models.TextField(blank=True, null=True, verbose_name="Внутренние заметки")
        
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f'Заказ #{self.id}: {self.title} - {self.user.username}'
    
    def get_status_display_with_color(self):
        for code, name in self.STATUS_CHOICES:
            if code == self.status:
                return name
        return self.status

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    
    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
    
    @property
    def is_manager(self):
        return self.role in ['manager', 'admin']
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_customer(self):
        return self.role == 'customer'
    
class Comment(models.Model):  
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        ordering = ['created_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий к #{self.request.id} от {self.author.username}'

class RequestHistory(models.Model): 
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='history', verbose_name="Заявка")
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Кто изменил")
    changed_field = models.CharField(max_length=50, verbose_name="Изменённое поле")
    old_value = models.CharField(max_length=255, blank=True, verbose_name="Старое значение")
    new_value = models.CharField(max_length=255, blank=True, verbose_name="Новое значение")
    change_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения")
    
    class Meta:
        ordering = ['-change_date']
        verbose_name = 'История заявки'
        verbose_name_plural = 'История заявок'
    
    def __str__(self):
        return f'Изменение #{self.request.id} - {self.changed_field}'