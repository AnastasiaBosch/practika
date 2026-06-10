from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from django.contrib.auth.models import User 
from django.http import HttpResponse  


def create_admin(request):
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        return HttpResponse('✅ Администратор создан!<br><br>Логин: admin<br>Пароль: admin123<br><br><a href="/admin/">Перейти в админ-панель</a>')
    else:
        return HttpResponse('⚠️ Администратор уже существует.<br><br><a href="/admin/">Перейти в админ-панель</a>')
    

urlpatterns = [
    
    path('create-admin/', create_admin),

    path('', lambda request: redirect('/catalog/', permanent=False)),
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),  
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)