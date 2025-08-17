"""
Django admin configuration for orders app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django_fsm import can_proceed

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem model.
    """
    model = OrderItem
    extra = 0
    readonly_fields = ('line_total', 'created_at')
    fields = (
        'product', 'product_name', 'product_sku', 'quantity', 
        'unit_price', 'line_total', 'created_at'
    )


class OrderStatusHistoryInline(admin.TabularInline):
    """
    Inline admin for OrderStatusHistory model.
    """
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('from_status', 'to_status', 'changed_by', 'reason', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Order model.
    """
    list_display = (
        'number', 'customer_email', 'status', 'grand_total', 
        'currency', 'created_at', 'paid_at'
    )
    list_filter = (
        'status', 'currency', 'created_at', 'paid_at', 
        'terms_accepted', 'newsletter_signup'
    )
    search_fields = (
        'number', 'user__email', 'guest_email', 
        'billing_first_name', 'billing_last_name',
        'shipping_first_name', 'shipping_last_name'
    )
    readonly_fields = (
        'id', 'number', 'created_at', 'updated_at', 
        'paid_at', 'shipped_at', 'delivered_at',
        'subtotal', 'tax_total', 'shipping_total', 'grand_total'
    )
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'number', 'user', 'guest_email', 'status')
        }),
        ('Billing Address', {
            'fields': (
                ('billing_first_name', 'billing_last_name'),
                'billing_company',
                'billing_address_line_1',
                'billing_address_line_2',
                ('billing_city', 'billing_state', 'billing_postal_code'),
                ('billing_country', 'billing_phone')
            )
        }),
        ('Shipping Address', {
            'fields': (
                ('shipping_first_name', 'shipping_last_name'),
                'shipping_company',
                'shipping_address_line_1',
                'shipping_address_line_2',
                ('shipping_city', 'shipping_state', 'shipping_postal_code'),
                ('shipping_country', 'shipping_phone')
            )
        }),
        ('Pricing', {
            'fields': (
                'currency',
                ('subtotal', 'tax_total'),
                ('shipping_total', 'discount_total'),
                'grand_total'
            )
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_accepted', 'newsletter_signup')
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
                ('paid_at', 'shipped_at', 'delivered_at')
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    actions = ['mark_as_paid', 'start_processing', 'ship_orders', 'cancel_orders']
    
    def mark_as_paid(self, request, queryset):
        """
        Mark selected orders as paid.
        """
        count = 0
        for order in queryset:
            if can_proceed(order.mark_as_paid):
                order.mark_as_paid()
                order.save()
                count += 1
        
        self.message_user(
            request,
            f'{count} orders marked as paid.'
        )
    mark_as_paid.short_description = 'Mark selected orders as paid'
    
    def start_processing(self, request, queryset):
        """
        Start processing selected orders.
        """
        count = 0
        for order in queryset:
            if can_proceed(order.start_processing):
                order.start_processing()
                order.save()
                count += 1
        
        self.message_user(
            request,
            f'{count} orders moved to processing.'
        )
    start_processing.short_description = 'Start processing selected orders'
    
    def ship_orders(self, request, queryset):
        """
        Mark selected orders as shipped.
        """
        count = 0
        for order in queryset:
            if can_proceed(order.ship):
                order.ship()
                order.save()
                count += 1
        
        self.message_user(
            request,
            f'{count} orders marked as shipped.'
        )
    ship_orders.short_description = 'Mark selected orders as shipped'
    
    def cancel_orders(self, request, queryset):
        """
        Cancel selected orders.
        """
        count = 0
        for order in queryset:
            if can_proceed(order.cancel):
                order.cancel()
                order.save()
                count += 1
        
        self.message_user(
            request,
            f'{count} orders canceled.'
        )
    cancel_orders.short_description = 'Cancel selected orders'
    
    def status_display(self, obj):
        """
        Display status with color coding.
        """
        colors = {
            'draft': 'gray',
            'pending_payment': 'orange',
            'paid': 'green',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'darkgreen',
            'canceled': 'red',
            'refunded': 'brown',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderItem model.
    """
    list_display = (
        'order', 'product', 'product_name', 'quantity', 
        'unit_price', 'line_total', 'created_at'
    )
    list_filter = ('created_at',)
    search_fields = (
        'order__number', 'product__name', 'product_name', 'product_sku'
    )
    readonly_fields = ('line_total', 'created_at')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderStatusHistory model.
    """
    list_display = (
        'order', 'from_status', 'to_status', 
        'changed_by', 'created_at'
    )
    list_filter = ('from_status', 'to_status', 'created_at')
    search_fields = (
        'order__number', 'changed_by__email', 'reason'
    )
    readonly_fields = ('created_at',)