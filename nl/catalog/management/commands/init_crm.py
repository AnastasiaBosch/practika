# catalog/management/commands/init_crm.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import UserRole

class Command(BaseCommand):
    help = 'Инициализация CRM: создание тестовых ролей'
    
    def handle(self, *args, **kwargs):
        # Создаем тестового сотрудника, если нет
        staff_user, created = User.objects.get_or_create(
            username='staff',
            defaults={
                'email': 'staff@example.com',
                'first_name': 'Иван',
                'last_name': 'Сотрудников',
                'is_staff': True  # Важно: даем доступ в админку
            }
        )
        if created:
            staff_user.set_password('staff123')
            staff_user.save()
        
        # Создаем или обновляем роль
        UserRole.objects.get_or_create(
            user=staff_user,
            defaults={'role': 'staff'}
        )
        self.stdout.write(self.style.SUCCESS('Создан тестовый сотрудник: staff/staff123'))
        
        # Создаем тестового курьера
        courier_user, created = User.objects.get_or_create(
            username='courier',
            defaults={
                'email': 'courier@example.com',
                'first_name': 'Петр',
                'last_name': 'Курьеров'
            }
        )
        if created:
            courier_user.set_password('courier123')
            courier_user.save()
        
        UserRole.objects.get_or_create(
            user=courier_user,
            defaults={'role': 'courier'}
        )
        self.stdout.write(self.style.SUCCESS('Создан тестовый курьер: courier/courier123'))
        
        # Создаем обычного пользователя для тестов
        customer_user, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'Алексей',
                'last_name': 'Покупателев'
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
        
        UserRole.objects.get_or_create(
            user=customer_user,
            defaults={'role': 'customer'}
        )
        self.stdout.write(self.style.SUCCESS('Создан тестовый покупатель: customer/customer123'))