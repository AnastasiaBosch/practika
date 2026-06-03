from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserRole, UserProfile, Request, RequestHistory

# Автоматическое создание роли "customer" при регистрации нового пользователя
@receiver(post_save, sender=User)
def create_user_role(sender, instance, created, **kwargs):
    if created:
        UserRole.objects.get_or_create(user=instance, defaults={'role': 'customer'})

# Автоматическое создание профиля пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# Автоматическое сохранение профиля
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# Запись в историю при создании заявки
@receiver(post_save, sender=Request)
def log_request_creation(sender, instance, created, **kwargs):
    if created:
        RequestHistory.objects.create(
            request=instance,
            changed_by=instance.user,
            changed_field='created',
            old_value='',
            new_value=f'Заявка #{instance.id} создана'
        )