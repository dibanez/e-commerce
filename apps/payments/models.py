"""
Payment models for the ecommerce application.
"""
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.orders.models import Order


class Payment(models.Model):
    """
    Payment model to track payment attempts and status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='order'
    )
    provider_code = models.CharField(
        'payment provider',
        max_length=50,
        help_text='Code of the payment provider used'
    )
    external_id = models.CharField(
        'external payment ID',
        max_length=255,
        blank=True,
        help_text='Payment ID from the payment provider'
    )
    amount = models.DecimalField(
        'amount',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        'currency',
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR'
    )
    status = models.CharField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    raw_request = models.JSONField(
        'raw request data',
        blank=True,
        null=True,
        help_text='Raw request data sent to payment provider'
    )
    raw_response = models.JSONField(
        'raw response data',
        blank=True,
        null=True,
        help_text='Raw response data from payment provider'
    )
    failure_reason = models.TextField(
        'failure reason',
        blank=True,
        help_text='Reason for payment failure'
    )
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    authorized_at = models.DateTimeField('authorized at', null=True, blank=True)
    captured_at = models.DateTimeField('captured at', null=True, blank=True)
    failed_at = models.DateTimeField('failed at', null=True, blank=True)

    class Meta:
        verbose_name = 'payment'
        verbose_name_plural = 'payments'
        db_table = 'payments_payment'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Payment {self.id} for Order {self.order.number}"

    @property
    def is_successful(self) -> bool:
        """
        Check if payment is successful (completed or captured).
        """
        return self.status in ['completed', 'captured']

    @property
    def is_pending(self) -> bool:
        """
        Check if payment is pending.
        """
        return self.status == 'pending'

    @property
    def is_failed(self) -> bool:
        """
        Check if payment failed.
        """
        return self.status in ['failed', 'canceled']

    @property
    def can_be_captured(self) -> bool:
        """
        Check if payment can be captured.
        """
        return self.status == 'authorized'

    @property
    def can_be_refunded(self) -> bool:
        """
        Check if payment can be refunded.
        """
        return self.status in ['completed', 'captured']

    @property
    def refunded_amount(self) -> Decimal:
        """
        Get total refunded amount.
        """
        return sum(
            transaction.amount 
            for transaction in self.transactions.filter(
                type='refund',
                success=True
            )
        )

    @property
    def refundable_amount(self) -> Decimal:
        """
        Get amount that can still be refunded.
        """
        if not self.can_be_refunded:
            return Decimal('0.00')
        
        return self.amount - self.refunded_amount

    def mark_as_authorized(self, external_id: str = '', raw_response: dict = None) -> None:
        """
        Mark payment as authorized.
        """
        self.status = 'authorized'
        self.authorized_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if raw_response:
            self.raw_response = raw_response
        self.save()

    def mark_as_captured(self, external_id: str = '', raw_response: dict = None) -> None:
        """
        Mark payment as captured.
        """
        self.status = 'captured'
        self.captured_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if raw_response:
            self.raw_response = raw_response
        self.save()

    def mark_as_completed(self, external_id: str = '', raw_response: dict = None) -> None:
        """
        Mark payment as completed.
        """
        self.status = 'completed'
        self.captured_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if raw_response:
            self.raw_response = raw_response
        self.save()

    def mark_as_failed(self, reason: str = '', raw_response: dict = None) -> None:
        """
        Mark payment as failed.
        """
        self.status = 'failed'
        self.failed_at = timezone.now()
        self.failure_reason = reason
        if raw_response:
            self.raw_response = raw_response
        self.save()


class Transaction(models.Model):
    """
    Transaction model to track individual payment operations.
    """
    TYPE_CHOICES = [
        ('authorize', 'Authorization'),
        ('capture', 'Capture'),
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('void', 'Void'),
        ('webhook', 'Webhook Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='payment'
    )
    type = models.CharField(
        'transaction type',
        max_length=20,
        choices=TYPE_CHOICES
    )
    external_id = models.CharField(
        'external transaction ID',
        max_length=255,
        blank=True,
        help_text='Transaction ID from payment provider'
    )
    amount = models.DecimalField(
        'amount',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(
        'currency',
        max_length=3,
        blank=True,
        default='EUR'
    )
    success = models.BooleanField('success', default=False)
    error_message = models.TextField('error message', blank=True)
    raw_request = models.JSONField(
        'raw request data',
        blank=True,
        null=True,
        help_text='Raw request data for this transaction'
    )
    raw_response = models.JSONField(
        'raw response data',
        blank=True,
        null=True,
        help_text='Raw response data for this transaction'
    )
    
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'transaction'
        verbose_name_plural = 'transactions'
        db_table = 'payments_transaction'
        ordering = ['-created_at']

    def __str__(self) -> str:
        status = 'Success' if self.success else 'Failed'
        return f"{self.get_type_display()} - {status} ({self.created_at})"

    @classmethod
    def create_transaction(
        cls,
        payment: Payment,
        transaction_type: str,
        amount: Decimal = None,
        external_id: str = '',
        success: bool = False,
        error_message: str = '',
        raw_request: dict = None,
        raw_response: dict = None
    ) -> 'Transaction':
        """
        Create a new transaction record.
        """
        return cls.objects.create(
            payment=payment,
            type=transaction_type,
            external_id=external_id,
            amount=amount,
            currency=payment.currency,
            success=success,
            error_message=error_message,
            raw_request=raw_request,
            raw_response=raw_response,
        )