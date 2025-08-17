"""
Base classes and interfaces for payment providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from django.http import HttpRequest


@dataclass
class PaymentInitResult:
    """
    Result of payment initialization.
    """
    redirect_url: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    render_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class PaymentWebhookResult:
    """
    Result of webhook processing.
    """
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    status: str = 'pending'  # pending, completed, failed, canceled
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    transaction_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class PaymentOperationResult:
    """
    Result of payment operations (capture, refund, etc.).
    """
    success: bool = False
    transaction_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    """
    
    # Provider identification
    code: str = ''
    display_name: str = ''
    description: str = ''
    
    # Provider capabilities
    supports_capture: bool = True
    supports_refund: bool = True
    supports_partial_refund: bool = True
    supports_webhooks: bool = True
    
    # Configuration
    test_mode: bool = True
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize payment provider with configuration.
        """
        self.config = config or {}
        self.test_mode = self.config.get('test_mode', True)
    
    @abstractmethod
    def start_payment(
        self,
        order,
        return_url: str,
        notify_url: str,
        **kwargs
    ) -> PaymentInitResult:
        """
        Start a payment process for an order.
        
        Args:
            order: Order instance
            return_url: URL where user should be redirected after payment
            notify_url: URL for payment notifications/webhooks
            **kwargs: Additional parameters
            
        Returns:
            PaymentInitResult with redirect URL or form data
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, request: HttpRequest) -> PaymentWebhookResult:
        """
        Handle webhook notification from payment provider.
        
        Args:
            request: HTTP request with webhook data
            
        Returns:
            PaymentWebhookResult with payment status information
        """
        pass
    
    def capture(
        self,
        order,
        amount: Optional[Decimal] = None,
        **kwargs
    ) -> PaymentOperationResult:
        """
        Capture a previously authorized payment.
        
        Args:
            order: Order instance
            amount: Amount to capture (None for full amount)
            **kwargs: Additional parameters
            
        Returns:
            PaymentOperationResult
        """
        if not self.supports_capture:
            return PaymentOperationResult(
                success=False,
                error_message=f"Provider {self.code} does not support capture"
            )
        
        # Default implementation - override in subclasses
        return PaymentOperationResult(
            success=False,
            error_message="Capture not implemented"
        )
    
    def refund(
        self,
        order,
        amount: Optional[Decimal] = None,
        reason: str = '',
        **kwargs
    ) -> PaymentOperationResult:
        """
        Refund a payment.
        
        Args:
            order: Order instance
            amount: Amount to refund (None for full amount)
            reason: Reason for refund
            **kwargs: Additional parameters
            
        Returns:
            PaymentOperationResult
        """
        if not self.supports_refund:
            return PaymentOperationResult(
                success=False,
                error_message=f"Provider {self.code} does not support refunds"
            )
        
        # Default implementation - override in subclasses
        return PaymentOperationResult(
            success=False,
            error_message="Refund not implemented"
        )
    
    def validate_webhook_signature(self, request: HttpRequest) -> bool:
        """
        Validate webhook signature/authentication.
        
        Args:
            request: HTTP request with webhook data
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Default implementation - always return True
        # Override in subclasses for actual signature validation
        return True
    
    def get_payment_status(self, payment_id: str) -> PaymentWebhookResult:
        """
        Get current status of a payment.
        
        Args:
            payment_id: Payment ID from provider
            
        Returns:
            PaymentWebhookResult with current status
        """
        # Default implementation - override in subclasses
        return PaymentWebhookResult(
            success=False,
            error_message="Status check not implemented"
        )
    
    def format_amount(self, amount: Decimal, currency: str = 'EUR') -> int:
        """
        Format amount for payment provider (usually in cents).
        
        Args:
            amount: Decimal amount
            currency: Currency code
            
        Returns:
            Amount in provider format (usually cents)
        """
        # Most providers use cents/minor units
        if currency.upper() in ['EUR', 'USD', 'GBP']:
            return int(amount * 100)
        
        # For currencies without minor units (e.g., JPY), return as-is
        return int(amount)
    
    def parse_amount(self, amount: int, currency: str = 'EUR') -> Decimal:
        """
        Parse amount from payment provider format to Decimal.
        
        Args:
            amount: Amount in provider format
            currency: Currency code
            
        Returns:
            Decimal amount
        """
        if currency.upper() in ['EUR', 'USD', 'GBP']:
            return Decimal(str(amount)) / 100
        
        return Decimal(str(amount))
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.code})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.code}>"