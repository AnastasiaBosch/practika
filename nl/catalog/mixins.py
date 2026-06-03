from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class SimpleRoleMixin(AccessMixin):
    """Миксин для проверки ролей пользователя"""
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Проверяем, есть ли у пользователя роль
        if not hasattr(request.user, 'role'):
            messages.error(request, "У пользователя нет роли")
            return redirect('index')
        
        # Проверяем, разрешена ли роль
        if request.user.role.role not in self.allowed_roles:
            messages.error(request, "Доступ запрещен")
            return redirect('index')
        
        return super().dispatch(request, *args, **kwargs)