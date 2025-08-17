"""
Orders models for the ecommerce application.
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_fsm import FSMField, transition

from apps.catalog.models import Product


class Order(models.Model):
    """
    Order model with FSM for status management.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]

    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(
        'order number',
        max_length=50,
        unique=True,
        blank=True,
        help_text='Human-readable order number'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='user'
    )
    guest_email = models.EmailField(
        'guest email',
        null=True,
        blank=True,
        help_text='Email for guest orders'
    )
    
    # Status management with FSM
    status = FSMField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        protected=True
    )
    
    # Billing information
    billing_first_name = models.CharField('billing first name', max_length=50)
    billing_last_name = models.CharField('billing last name', max_length=50)
    billing_company = models.CharField('billing company', max_length=100, blank=True)
    billing_address_line_1 = models.CharField('billing address line 1', max_length=255)
    billing_address_line_2 = models.CharField('billing address line 2', max_length=255, blank=True)
    billing_city = models.CharField('billing city', max_length=100)
    billing_state = models.CharField('billing state/province', max_length=100)
    billing_postal_code = models.CharField('billing postal code', max_length=20)
    billing_country = models.CharField('billing country', max_length=2, default='ES')
    billing_phone = models.CharField('billing phone', max_length=20, blank=True)
    
    # Shipping information
    shipping_first_name = models.CharField('shipping first name', max_length=50)
    shipping_last_name = models.CharField('shipping last name', max_length=50)
    shipping_company = models.CharField('shipping company', max_length=100, blank=True)
    shipping_address_line_1 = models.CharField('shipping address line 1', max_length=255)
    shipping_address_line_2 = models.CharField('shipping address line 2', max_length=255, blank=True)
    shipping_city = models.CharField('shipping city', max_length=100)
    shipping_state = models.CharField('shipping state/province', max_length=100)
    shipping_postal_code = models.CharField('shipping postal code', max_length=20)
    shipping_country = models.CharField('shipping country', max_length=2, default='ES')
    shipping_phone = models.CharField('shipping phone', max_length=20, blank=True)
    
    # Pricing
    currency = models.CharField(
        'currency',
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR'
    )
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_total = models.DecimalField(
        'tax total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    shipping_total = models.DecimalField(
        'shipping total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_total = models.DecimalField(
        'discount total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    grand_total = models.DecimalField(
        'grand total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Additional information
    notes = models.TextField('notes', blank=True)
    terms_accepted = models.BooleanField('terms accepted', default=False)
    newsletter_signup = models.BooleanField('newsletter signup', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    paid_at = models.DateTimeField('paid at', null=True, blank=True)
    shipped_at = models.DateTimeField('shipped at', null=True, blank=True)
    delivered_at = models.DateTimeField('delivered at', null=True, blank=True)

    class Meta:
        verbose_name = 'order'
        verbose_name_plural = 'orders'
        db_table = 'orders_order'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order {self.number}"

    def save(self, *args, **kwargs) -> None:
        if not self.number:
            self.number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self) -> str:
        """
        Generate a human-readable order number.
        """
        from django.conf import settings
        prefix = getattr(settings, 'ORDER_NUMBER_PREFIX', 'ORD')
        timestamp = timezone.now().strftime('%Y%m')
        
        # Get the next sequential number for this month
        last_order = Order.objects.filter(
            number__startswith=f"{prefix}-{timestamp}"
        ).order_by('-number').first()
        
        if last_order:
            try:
                last_number = int(last_order.number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}-{timestamp}-{next_number:04d}"

    def get_absolute_url(self) -> str:
        return reverse('orders:order_detail', kwargs={'number': self.number})

    @property
    def customer_email(self) -> str:
        """
        Get customer email (user email or guest email).
        """
        if self.user:
            return self.user.email
        return self.guest_email or ''

    @property
    def customer_name(self) -> str:
        """
        Get customer full name from billing information.
        """
        return f"{self.billing_first_name} {self.billing_last_name}".strip()

    @property
    def shipping_address(self) -> str:
        """
        Get formatted shipping address.
        """
        lines = [
            f"{self.shipping_first_name} {self.shipping_last_name}",
        ]
        if self.shipping_company:
            lines.append(self.shipping_company)
        lines.extend([
            self.shipping_address_line_1,
        ])
        if self.shipping_address_line_2:
            lines.append(self.shipping_address_line_2)
        lines.append(f"{self.shipping_city}, {self.shipping_state} {self.shipping_postal_code}")
        lines.append(self.shipping_country)
        return '\n'.join(lines)

    @property
    def billing_address(self) -> str:
        """
        Get formatted billing address.
        """
        lines = [
            f"{self.billing_first_name} {self.billing_last_name}",
        ]
        if self.billing_company:
            lines.append(self.billing_company)
        lines.extend([
            self.billing_address_line_1,
        ])
        if self.billing_address_line_2:
            lines.append(self.billing_address_line_2)
        lines.append(f"{self.billing_city}, {self.billing_state} {self.billing_postal_code}")
        lines.append(self.billing_country)
        return '\n'.join(lines)

    def calculate_totals(self) -> None:
        """
        Calculate order totals based on items.
        """
        self.subtotal = sum(item.line_total for item in self.items.all())
        
        # Simple tax calculation (you can implement more complex logic)
        tax_rate = Decimal('0.21')  # 21% VAT for Spain
        self.tax_total = self.subtotal * tax_rate
        
        # Simple shipping calculation
        if self.subtotal >= Decimal('50.00'):
            self.shipping_total = Decimal('0.00')  # Free shipping over 50€
        else:
            self.shipping_total = Decimal('5.95')  # Standard shipping
        
        self.grand_total = self.subtotal + self.tax_total + self.shipping_total - self.discount_total

    # FSM Transitions
    @transition(field=status, source='draft', target='pending_payment')
    def submit(self):
        """
        Submit order for payment.
        """
        if not self.terms_accepted:
            raise ValueError("Terms must be accepted")
        
        if not self.items.exists():
            raise ValueError("Order must have items")
        
        self.calculate_totals()

    @transition(field=status, source='pending_payment', target='paid')
    def mark_as_paid(self):
        """
        Mark order as paid.
        """
        self.paid_at = timezone.now()

    @transition(field=status, source='paid', target='processing')
    def start_processing(self):
        """
        Start processing the order.
        """
        pass

    @transition(field=status, source='processing', target='shipped')
    def ship(self):
        """
        Mark order as shipped.
        """
        self.shipped_at = timezone.now()

    @transition(field=status, source='shipped', target='delivered')
    def deliver(self):
        """
        Mark order as delivered.
        """
        self.delivered_at = timezone.now()

    @transition(field=status, source=['draft', 'pending_payment', 'paid', 'processing'], target='canceled')
    def cancel(self):
        """
        Cancel the order.
        """
        pass

    @transition(field=status, source='paid', target='refunded')
    def refund(self):
        """
        Refund the order.
        """
        pass


class OrderItem(models.Model):
    """
    Order item model representing a product in an order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='order'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='product'
    )
    
    # Snapshot of product data at time of order
    product_name = models.CharField('product name', max_length=200)
    product_sku = models.CharField('product SKU', max_length=50)
    product_description = models.TextField('product description', blank=True)
    
    quantity = models.PositiveIntegerField(
        'quantity',
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        'unit price',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    line_total = models.DecimalField(
        'line total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'order item'
        verbose_name_plural = 'order items'
        db_table = 'orders_orderitem'
        unique_together = [['order', 'product']]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name} in {self.order.number}"

    def save(self, *args, **kwargs) -> None:
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        
        # Take snapshot of product data if not already set
        if not self.product_name and self.product:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
            self.product_description = self.product.short_description or self.product.description
        
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Track order status changes for auditing.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='order'
    )
    from_status = models.CharField(
        'from status',
        max_length=20,
        choices=Order.STATUS_CHOICES,
        null=True,
        blank=True
    )
    to_status = models.CharField(
        'to status',
        max_length=20,
        choices=Order.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='changed by'
    )
    reason = models.TextField('reason', blank=True)
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'order status history'
        verbose_name_plural = 'order status histories'
        db_table = 'orders_orderstatushistory'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.order.number}: {self.from_status} → {self.to_status}"