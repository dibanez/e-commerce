"""
Django admin configuration for payments app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Payment, Transaction


class TransactionInline(admin.TabularInline):
    """
    Inline admin for Transaction model.
    """
    model = Transaction
    extra = 0
    readonly_fields = ('created_at',)
    fields = (
        'type', 'external_id', 'amount', 'currency', 
        'success', 'error_message', 'created_at'
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model.
    """
    list_display = (
        'id_short', 'order', 'provider_code', 'amount', 
        'currency', 'status_display', 'created_at'
    )
    list_filter = (
        'status', 'provider_code', 'currency', 'created_at'
    )
    search_fields = (
        'id', 'order__number', 'external_id', 'order__user__email'
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'authorized_at', 
        'captured_at', 'failed_at', 'refunded_amount', 'refundable_amount'
    )
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'id', 'order', 'provider_code', 'external_id'
            )
        }),
        ('Amount', {
            'fields': (
                ('amount', 'currency'), 'refunded_amount', 'refundable_amount'
            )
        }),
        ('Status', {
            'fields': ('status', 'failure_reason')
        }),
        ('Data', {
            'fields': ('raw_request', 'raw_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
                ('authorized_at', 'captured_at', 'failed_at')
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TransactionInline]
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def id_short(self, obj):
        """
        Display shortened payment ID.
        """
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'Payment ID'
    
    def status_display(self, obj):
        """
        Display status with color coding.
        """
        colors = {
            'pending': 'orange',
            'authorized': 'blue',
            'captured': 'green',
            'completed': 'darkgreen',
            'failed': 'red',
            'canceled': 'gray',
            'refunded': 'brown',
            'partially_refunded': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def mark_as_completed(self, request, queryset):
        """
        Mark selected payments as completed.
        """
        count = 0
        for payment in queryset:
            if payment.status in ['pending', 'authorized']:
                payment.mark_as_completed()
                count += 1
        
        self.message_user(
            request,
            f'{count} payments marked as completed.'
        )
    mark_as_completed.short_description = 'Mark selected payments as completed'
    
    def mark_as_failed(self, request, queryset):
        """
        Mark selected payments as failed.
        """
        count = 0
        for payment in queryset:
            if payment.status == 'pending':
                payment.mark_as_failed('Manually marked as failed')
                count += 1
        
        self.message_user(
            request,
            f'{count} payments marked as failed.'
        )
    mark_as_failed.short_description = 'Mark selected payments as failed'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction model.
    """
    list_display = (
        'id_short', 'payment', 'type', 'amount', 
        'currency', 'success_display', 'created_at'
    )
    list_filter = (
        'type', 'success', 'currency', 'created_at'
    )
    search_fields = (
        'id', 'payment__id', 'external_id', 'payment__order__number'
    )
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'id', 'payment', 'type', 'external_id'
            )
        }),
        ('Amount', {
            'fields': (('amount', 'currency'),)
        }),
        ('Result', {
            'fields': ('success', 'error_message')
        }),
        ('Data', {
            'fields': ('raw_request', 'raw_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def id_short(self, obj):
        """
        Display shortened transaction ID.
        """
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'Transaction ID'
    
    def success_display(self, obj):
        """
        Display success status with color.
        """
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Success</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Failed</span>'
            )
    success_display.short_description = 'Success'