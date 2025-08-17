"""
Django admin configuration for users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Address, User, UserProfile


class AddressInline(admin.TabularInline):
    """
    Inline admin for Address model.
    """
    model = Address
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    """
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    inlines = [AddressInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ('user', 'phone', 'newsletter_subscription', 'created_at')
    list_filter = ('newsletter_subscription', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """
    Admin configuration for Address model.
    """
    list_display = ('user', 'type', 'full_name', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('type', 'country', 'is_default', 'created_at')
    search_fields = (
        'user__email', 
        'first_name', 
        'last_name', 
        'city', 
        'address_line_1'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User'), {
            'fields': ('user', 'type', 'is_default')
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'company', 'phone')
        }),
        (_('Address'), {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )