from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Request, Category, Comment, RequestHistory, UserRole

class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name="Тестовая категория")
        self.assertEqual(str(category), "Тестовая категория")

class UserRoleModelTest(TestCase):
    def test_user_role_creation(self):
        user = User.objects.create_user(username="testuser", password="12345")
        role, created = UserRole.objects.update_or_create(
            user=user,
            defaults={'role': 'customer'}
        )
        self.assertEqual(role.role, "customer")
        self.assertTrue(role.is_customer)
        self.assertFalse(role.is_manager)

class RequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="client", password="12345")
        self.category = Category.objects.create(name="Тест")
        
    def test_request_creation(self):
        request = Request.objects.create(
            user=self.user,
            title="Тестовая заявка",
            description="Тестовое описание",
            category=self.category,
            priority="medium"
        )
        self.assertEqual(request.status, "new")
        self.assertEqual(request.get_status_display_with_color(), "🟡 Создан")
        
    def test_request_default_status(self):
        request = Request.objects.create(
            user=self.user,
            title="Тест",
            description="Описание"
        )
        self.assertEqual(request.status, "new")

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.request = Request.objects.create(
            user=self.user,
            title="Тест",
            description="Описание"
        )
        
    def test_comment_creation(self):
        comment = Comment.objects.create(
            request=self.request,
            author=self.user,
            text="Тестовый комментарий"
        )
        self.assertEqual(str(comment), f'Комментарий к #{self.request.id} от testuser')

class RequestHistoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.request = Request.objects.create(
            user=self.user,
            title="Тест",
            description="Описание"
        )
        
    def test_history_creation(self):
        history = RequestHistory.objects.create(
            request=self.request,
            changed_by=self.user,
            changed_field="status",
            old_value="new",
            new_value="in_progress"
        )
        self.assertEqual(str(history), f'Изменение #{self.request.id} - status')

class RegistrationTest(TestCase):
    def test_register_page(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)

class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        
    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': '12345'
        })
        self.assertEqual(response.status_code, 302)

class RequestCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="client", password="12345")
        # Используем update_or_create
        UserRole.objects.update_or_create(user=self.user, defaults={'role': 'customer'})
        self.client.login(username="client", password="12345")
        
    def test_create_request_page(self):
        response = self.client.get(reverse('request_create'))
        self.assertEqual(response.status_code, 200)
        
    def test_create_request_success(self):
        response = self.client.post(reverse('request_create'), {
            'title': 'Тестовая заявка',
            'description': 'Тестовое описание',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Request.objects.count(), 1)

class RequestListViewTest(TestCase):
    def setUp(self):
        self.client1 = User.objects.create_user(username="client1", password="12345")
        self.client2 = User.objects.create_user(username="client2", password="12345")
        UserRole.objects.update_or_create(user=self.client1, defaults={'role': 'customer'})
        UserRole.objects.update_or_create(user=self.client2, defaults={'role': 'customer'})
        
        self.request1 = Request.objects.create(
            user=self.client1,
            title="Заявка клиента1",
            description="Описание1"
        )
        self.request2 = Request.objects.create(
            user=self.client2,
            title="Заявка клиента2",
            description="Описание2"
        )
        
    def test_client_sees_only_own_requests(self):
        self.client.login(username="client1", password="12345")
        response = self.client.get(reverse('request_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

class ManagerAccessTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager", password="12345")
        UserRole.objects.update_or_create(user=self.manager, defaults={'role': 'manager'})
        self.client.login(username="manager", password="12345")
        
        self.client_user = User.objects.create_user(username="client", password="12345")
        UserRole.objects.update_or_create(user=self.client_user, defaults={'role': 'customer'})
        self.request = Request.objects.create(
            user=self.client_user,
            title="Чужая заявка",
            description="Описание"
        )
        
    def test_manager_sees_all_requests(self):
        response = self.client.get(reverse('request_list'))
        self.assertEqual(len(response.context['object_list']), 1)
        
    def test_change_status_page_access(self):
        response = self.client.get(reverse('change_request_status', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)
        
    def test_assign_executor_page_access(self):
        response = self.client.get(reverse('assign_executor', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)

class RolePermissionsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="12345")
        self.manager = User.objects.create_user(username="manager", password="12345")
        self.customer = User.objects.create_user(username="customer", password="12345")
        
        UserRole.objects.update_or_create(user=self.admin, defaults={'role': 'admin'})
        UserRole.objects.update_or_create(user=self.manager, defaults={'role': 'manager'})
        UserRole.objects.update_or_create(user=self.customer, defaults={'role': 'customer'})
        
        self.request = Request.objects.create(
            user=self.customer,
            title="Тест",
            description="Описание"
        )
        
    def test_customer_cannot_change_status(self):
        self.client.login(username="customer", password="12345")
        response = self.client.get(reverse('change_request_status', args=[self.request.id]))
        self.assertEqual(response.status_code, 302)
        
    def test_manager_can_change_status(self):
        self.client.login(username="manager", password="12345")
        response = self.client.get(reverse('change_request_status', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)
        
    def test_admin_can_change_status(self):
        self.client.login(username="admin", password="12345")
        response = self.client.get(reverse('change_request_status', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)