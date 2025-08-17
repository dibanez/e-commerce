"""
Django admin configuration for cart app.
"""
from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """
    Inline admin for CartItem model.
    """
    model = CartItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    fields = ('product', 'quantity', 'unit_price', 'total_price', 'created_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin configuration for Cart model.
    """
    list_display = ('__str__', 'user', 'session_key_short', 'total_items', 'subtotal', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'subtotal')
    
    inlines = [CartItemInline]
    
    def session_key_short(self, obj):
        """
        Display shortened session key.
        """
        if obj.session_key:
            return f"{obj.session_key[:8]}..."
        return '-'
    session_key_short.short_description = 'Session Key'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key')
        }),
        ('Summary', {
            'fields': ('total_items', 'subtotal'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for CartItem model.
    """
    list_display = ('cart', 'product', 'quantity', 'unit_price', 'total_price', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    
    fieldsets = (
        (None, {
            'fields': ('cart', 'product', 'quantity', 'unit_price')
        }),
        ('Calculated', {
            'fields': ('total_price',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )