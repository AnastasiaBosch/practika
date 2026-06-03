from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Request, Comment, Category


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует.')
        if len(username) < 3:
            raise ValidationError('Имя пользователя должно содержать не менее 3 символов.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают.')
        if len(password1) < 8:
            raise ValidationError('Пароль должен содержать не менее 8 символов.')
        return password2
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Только буквы, цифры и @/./+/-/_.'
        self.fields['password1'].help_text = 'Пароль должен содержать не менее 8 символов.'
        self.fields['password2'].help_text = 'Введите тот же пароль ещё раз.'
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['title', 'description', 'category'] 
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите тему заявки'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите проблему или задачу...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['description'].required = True


class RequestStatusForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['status', 'internal_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Внутренние заметки (видны только менеджерам)...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['internal_notes'].required = False


class RequestAssignForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['executor', 'priority', 'deadline']
        widgets = {
            'executor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deadline'].required = False
        self.fields['executor'].required = False
        
        # Ограничиваем выбор исполнителей только менеджерами и админами
        from .models import UserRole
        manager_ids = UserRole.objects.filter(role__in=['manager', 'admin']).values_list('user_id', flat=True)
        self.fields['executor'].queryset = User.objects.filter(id__in=manager_ids)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите комментарий...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = True
        self.fields['text'].label = 'Комментарий'


class RequestFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Все статусы')] + list(Request.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', 'Все приоритеты')] + list(Request.PRIORITY_CHOICES)
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по теме или описанию...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        required=False,
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label = 'Категория'
        self.fields['category'].empty_label = 'Все категории'