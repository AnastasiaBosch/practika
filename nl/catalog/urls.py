from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('requests/', views.RequestListView.as_view(), name='request_list'),
    path('request/<int:pk>/', views.RequestDetailView.as_view(), name='request_detail'),
    path('request/create/', views.RequestCreateView.as_view(), name='request_create'),
    path('request/<int:pk>/edit/', views.RequestUpdateView.as_view(), name='request_edit'),
    path('request/<int:pk>/change-status/', views.change_request_status, name='change_request_status'),
    path('request/<int:pk>/assign-executor/', views.assign_executor, name='assign_executor'),
    path('request/<int:pk>/add-comment/', views.add_comment, name='add_comment'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('manager/user/<int:user_id>/requests/', views.user_requests, name='user_requests'),
    path('contact-admin/', views.contact_admin, name='contact_admin'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)