# apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role
from django import forms

class UserCreationForm(forms.ModelForm):
    """Форма для создания пользователя"""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('login', 'role', 'manid', 'status')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Форма для изменения пользователя"""
    class Meta:
        model = User
        fields = '__all__'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['text', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['text']
    readonly_fields = ['created_at']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    
    # Убираем filter_horizontal, так как у нас нет groups и user_permissions
    filter_horizontal = []
    
    list_display = ['login', 'get_role_name', 'manid', 'status', 'is_superuser', 'date_joined']
    list_filter = ['status', 'is_superuser', 'role', 'date_joined']
    search_fields = ['login', 'manid']
    ordering = ['login']
    
    # Убираем groups и user_permissions из fieldsets
    fieldsets = (
        (None, {'fields': ('login', 'password')}),
        ('Персональная информация', {'fields': ('manid',)}),
        ('Роли и статусы', {'fields': ('role', 'status')}),
        ('Разрешения', {'fields': ('is_superuser',)}),  # Убрали groups, user_permissions
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'password1', 'password2', 'role', 'manid', 'status', 'is_superuser'),
        }),
    )
    
    def get_role_name(self, obj):
        return obj.role.text if obj.role else 'Не назначена'
    get_role_name.short_description = 'Роль'
    get_role_name.admin_order_field = 'role__text'

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data and form.cleaned_data['password']:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
