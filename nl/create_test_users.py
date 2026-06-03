import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nl.settings')
django.setup()

from django.contrib.auth.models import User
from catalog.models import UserRole, Category

def create_test_users():
    print("=" * 50)
    print("Создание тестовых пользователей...")
    print("=" * 50)
    
    # Создаём категории (если их нет)
    categories = ['Техническая проблема', 'Финансовый вопрос', 'Кадровый вопрос', 'Закупка оборудования', 'Другое']
    for cat_name in categories:
        cat, created = Category.objects.get_or_create(name=cat_name)
        if created:
            print(f"   Создана категория: {cat_name}")
    
    # Данные для тестовых пользователей
    users_data = [
        {
            'username': 'manager',
            'email': 'manager@example.com',
            'password': 'manager123',
            'first_name': 'Мария',
            'last_name': 'Менеджерова',
            'role': 'manager'
        },
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'admin123',
            'first_name': 'Админ',
            'last_name': 'Админов',
            'role': 'admin'
        },
        {
            'username': 'client',
            'email': 'client@example.com',
            'password': 'client123',
            'first_name': 'Клиент',
            'last_name': 'Клиентов',
            'role': 'customer'
        },
        {
            'username': 'client2',
            'email': 'client2@example.com',
            'password': 'client123',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'role': 'customer'
        }
    ]
    
    for user_data in users_data:
        # Удаляем пользователя, если существует (вместе с ролью)
        try:
            old_user = User.objects.get(username=user_data['username'])
            # Удаляем роль
            UserRole.objects.filter(user=old_user).delete()
            # Удаляем пользователя
            old_user.delete()
            print(f"   Удалён старый пользователь: {user_data['username']}")
        except User.DoesNotExist:
            pass
        
        # Создаём пользователя
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            is_staff=(user_data['role'] in ['manager', 'admin']),
            is_active=True
        )
        
        # Создаём роль (сигнал мог создать роль customer, поэтому используем update_or_create)
        role, created = UserRole.objects.update_or_create(
            user=user,
            defaults={'role': user_data['role']}
        )
        
        print(f"   Создан {user_data['role']}: {user_data['username']} / {user_data['password']}")
    
    print("\n" + "=" * 50)
    print("Тестовые пользователи созданы!")
    print("=" * 50)
    print("\n Доступные пользователи:")
    print("   Администратор:  admin    / admin123")
    print("   Менеджер:       manager  / manager123")
    print("   Клиент:         client   / client123")
    print("   Клиент 2:       client2  / client123")
    print("\n Категории созданы автоматически.")

if __name__ == '__main__':
    create_test_users()