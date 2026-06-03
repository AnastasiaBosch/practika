from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.views.generic import TemplateView
from .models import Request, Category, Comment, RequestHistory, UserRole, UserProfile
from .forms import RequestForm, CommentForm, RequestStatusForm, RequestAssignForm, UserRegisterForm
from .mixins import SimpleRoleMixin
from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

def logout_view(request):
    auth_logout(request)
    return redirect('login')


def index(request):
    context = {}
    
    if request.user.is_authenticated:
        user_requests = Request.objects.filter(user=request.user)
        context['total_my_requests'] = user_requests.count()
        context['my_active_requests'] = user_requests.filter(status__in=['new', 'in_progress']).count()
        context['my_completed_requests'] = user_requests.filter(status='completed').count()
        context['recent_requests'] = user_requests.order_by('-created_date')[:5]
        
        if hasattr(request.user, 'role') and (request.user.role.is_manager or request.user.role.is_admin):
            context['total_all_requests'] = Request.objects.count()
            context['new_requests'] = Request.objects.filter(status='new').count()
            context['in_progress_requests'] = Request.objects.filter(status='in_progress').count()
            context['unassigned_requests'] = Request.objects.filter(executor__isnull=True).exclude(status='completed').count()
            context['unassigned_requests_list'] = Request.objects.filter(executor__isnull=True).exclude(status='completed')[:5]
    
    return render(request, 'index.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Аккаунт {user.username} создан! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    user_requests = Request.objects.filter(user=request.user)
    
    context = {
        'total_requests': user_requests.count(),
        'active_requests': user_requests.filter(status__in=['new', 'in_progress']).count(),
        'completed_requests': user_requests.filter(status='completed').count(),
        'new_requests': user_requests.filter(status='new').count(),
        'rejected_requests': user_requests.filter(status='rejected').count(),
        'recent_requests': user_requests.order_by('-created_date')[:10],
    }
    
    if hasattr(request.user, 'role') and (request.user.role.is_manager or request.user.role.is_admin):
        context['assigned_requests'] = Request.objects.filter(executor=request.user).order_by('-created_date')[:10]
    
    return render(request, 'profile.html', context)


class RequestListView(LoginRequiredMixin, generic.ListView):
    model = Request
    paginate_by = 10
    template_name = 'requests/request_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin):
            pass
        else:
            queryset = queryset.filter(user=user)
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
         # Фильтр по статусу (только для менеджеров)
        status = self.request.GET.get('status', '')
        if status and (hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)):
            queryset = queryset.filter(status=status)
        
        # Фильтр по категории
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Фильтр по приоритету (только для менеджеров)
        priority = self.request.GET.get('priority', '')
        if priority and (hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)):
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_manager = hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)
    
        context['categories'] = Category.objects.all()
        
        # Статусы и приоритеты показываем только менеджерам
        if is_manager:
            context['status_choices'] = Request.STATUS_CHOICES
            context['priority_choices'] = Request.PRIORITY_CHOICES
        else:
            context['status_choices'] = []
            context['priority_choices'] = []
        
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'priority': self.request.GET.get('priority', ''),
        }
        context['is_manager'] = is_manager
        
        return context

class RequestDetailView(LoginRequiredMixin, generic.DetailView):
    model = Request
    template_name = 'requests/request_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        context['history'] = self.object.history.all()
        
        user = self.request.user
        context['can_edit'] = hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)
        
        context['can_change_status'] = hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)
        context['can_assign'] = hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)
        
        return context


class RequestCreateView(LoginRequiredMixin, generic.CreateView):
    model = Request
    form_class = RequestForm
    template_name = 'requests/request_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.priority = 'medium'
        response = super().form_valid(form)
        
        RequestHistory.objects.create(
            request=self.object,
            changed_by=self.request.user,
            changed_field='created',
            old_value='',
            new_value='Заявка создана'
        )
        messages.success(self.request, f'Заявка "{self.object.title}" успешно создана!')
        return response
    
    def form_invalid(self, form):
        print("=" * 50)
        print("ФОРМА НЕ ВАЛИДНА!")
        print("Ошибки:", form.errors)
        print("=" * 50)
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('request_detail', args=[self.object.id])

class RequestUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Request
    form_class = RequestForm
    template_name = 'requests/request_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        
        # Только менеджеры и админы могут редактировать заявки
        if not (hasattr(user, 'role') and (user.role.is_manager or user.role.is_admin)):
            messages.error(request, 'У вас нет прав на редактирование этой заявки')
            return redirect('request_detail', pk=obj.pk)
    
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Заявка "{self.object.title}" обновлена')
        return response
    
    def get_success_url(self):
        return reverse('request_detail', args=[self.object.id])


@login_required
def change_request_status(request, pk):
    request_obj = get_object_or_404(Request, id=pk)
    
    if not (hasattr(request.user, 'role') and (request.user.role.is_manager or request.user.role.is_admin)):
        messages.error(request, 'Только менеджеры могут изменять статус заявок')
        return redirect('request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RequestStatusForm(request.POST, instance=request_obj)
        if form.is_valid():
            old_status = request_obj.status
            new_status = form.cleaned_data['status']
            form.save()
            
            if old_status != new_status:
                RequestHistory.objects.create(
                    request=request_obj,
                    changed_by=request.user,
                    changed_field='status',
                    old_value=old_status,
                    new_value=new_status
                )
                messages.success(request, f'Статус заявки изменён')
            return redirect('request_detail', pk=pk)
    else:
        form = RequestStatusForm(instance=request_obj)
    
    context = {
        'request_obj': request_obj,
        'form': form,
        'status_choices': Request.STATUS_CHOICES,
        'history': RequestHistory.objects.filter(request=request_obj)[:5]
    }
    return render(request, 'requests/change_status.html', context)


@login_required
def assign_executor(request, pk):
    request_obj = get_object_or_404(Request, id=pk)
    
    if not (hasattr(request.user, 'role') and (request.user.role.is_manager or request.user.role.is_admin)):
        messages.error(request, 'Только менеджеры могут назначать исполнителей')
        return redirect('request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RequestAssignForm(request.POST, instance=request_obj)
        if form.is_valid():
            old_executor = request_obj.executor
            form.save()
            
            if old_executor != request_obj.executor:
                RequestHistory.objects.create(
                    request=request_obj,
                    changed_by=request.user,
                    changed_field='executor',
                    old_value=str(old_executor) if old_executor else 'Не назначен',
                    new_value=str(request_obj.executor) if request_obj.executor else 'Не назначен'
                )
                messages.success(request, f'Исполнитель назначен: {request_obj.executor}')
            return redirect('request_detail', pk=pk)
    else:
        form = RequestAssignForm(instance=request_obj)
    
    managers = UserRole.objects.filter(role__in=['manager', 'admin']).select_related('user')
    managers_list = [
        {'id': m.user.id, 'username': m.user.username, 'role': m.get_role_display()}
        for m in managers
    ]
    
    return render(request, 'requests/assign_executor.html', {
        'request_obj': request_obj,
        'form': form,
        'available_managers': managers,
        'managers_json': json.dumps(managers_list),
    })


@login_required
def add_comment(request, pk):
    request_obj = get_object_or_404(Request, id=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.request = request_obj
            comment.author = request.user
            comment.save()
            
            RequestHistory.objects.create(
                request=request_obj,
                changed_by=request.user,
                changed_field='comment',
                old_value='',
                new_value=f'Добавлен комментарий: {comment.text[:50]}...'
            )
            messages.success(request, 'Комментарий добавлен')
        
        return redirect('request_detail', pk=pk)
    
    return redirect('request_detail', pk=pk)


class ManagerDashboardView(SimpleRoleMixin, TemplateView):
    template_name = 'requests/manager/dashboard.html'
    allowed_roles = ['manager', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        now = timezone.now()
        month_ago = now - timedelta(days=30)
        
        context['total_requests'] = Request.objects.count()
        context['new_requests'] = Request.objects.filter(status='new').count()
        context['in_progress_requests'] = Request.objects.filter(status='in_progress').count()
        context['completed_requests'] = Request.objects.filter(status='completed').count()
        context['rejected_requests'] = Request.objects.filter(status='rejected').count()
        context['completed_this_month'] = Request.objects.filter(status='completed', created_date__gte=month_ago).count()
        
        total = context['total_requests'] or 1
        context['new_requests_percent'] = round(context['new_requests'] / total * 100, 1)
        context['in_progress_percent'] = round(context['in_progress_requests'] / total * 100, 1)
        context['completed_percent'] = round(context['completed_requests'] / total * 100, 1)
        context['rejected_percent'] = round(context['rejected_requests'] / total * 100, 1)
        
        unassigned = Request.objects.filter(executor__isnull=True).exclude(status='completed')
        context['unassigned_requests'] = unassigned.count()
        context['unassigned_requests_list'] = unassigned[:10]
        
        context['overdue_requests'] = Request.objects.filter(
            deadline__lt=now,
            status__in=['new', 'in_progress']
        ).count()
        
        context['total_users'] = User.objects.count()
        
        context['top_users'] = User.objects.annotate(
            total=Count('requests'),
            completed=Count('requests', filter=Q(requests__status='completed')),
            active=Count('requests', filter=Q(requests__status__in=['new', 'in_progress']))
        ).filter(total__gt=0).order_by('-total')[:10]
        
        return context

@login_required
def user_requests(request, user_id):
    """Просмотр заявок конкретного пользователя (только для менеджеров)"""
    if not (hasattr(request.user, 'role') and (request.user.role.is_manager or request.user.role.is_admin)):
        messages.error(request, 'Доступ запрещён')
        return redirect('request_list')
    
    customer = get_object_or_404(User, id=user_id)
    requests_list = Request.objects.filter(user=customer).order_by('-created_date')
    
    return render(request, 'requests/user_requests.html', {
        'customer': customer,
        'object_list': requests_list,
        'total_requests': requests_list.count(),
        'new_requests': requests_list.filter(status='new').count(),
        'in_progress_requests': requests_list.filter(status='in_progress').count(),
        'completed_requests': requests_list.filter(status='completed').count(),
        'rejected_requests': requests_list.filter(status='rejected').count(),
    })
@login_required
def contact_admin(request):
    return render(request, 'requests/contact_admin.html')
