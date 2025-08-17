"""
Dummy payment provider for development and testing.
"""
import json
import random
import time
from decimal import Decimal
from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

from ..base import PaymentProvider, PaymentInitResult, PaymentWebhookResult, PaymentOperationResult


class DummyProvider(PaymentProvider):
    """
    Dummy payment provider for development and testing.
    
    This provider simulates payment processing without actually charging any cards.
    It's useful for development, testing, and demonstrations.
    """
    
    code = 'dummy'
    display_name = 'Dummy Payment (Development)'
    description = 'Fake payment provider for development and testing'
    
    # Capabilities
    supports_capture = True
    supports_refund = True
    supports_partial_refund = True
    supports_webhooks = True
    
    def __init__(self, config=None):
        super().__init__(config)
        
        # Get success rate from Django settings first, then allow config to override
        default_success_rate = 100
        if hasattr(settings, 'DUMMY_PAYMENT_SUCCESS_RATE'):
            default_success_rate = int(settings.DUMMY_PAYMENT_SUCCESS_RATE)
        
        # Configuration options (config can override settings)
        self.success_rate = self.config.get('success_rate', default_success_rate)  # Percentage
        self.processing_delay = self.config.get('processing_delay', 0)  # Seconds
        self.auto_capture = self.config.get('auto_capture', True)
    
    def start_payment(self, order, return_url: str, notify_url: str, **kwargs) -> PaymentInitResult:
        """
        Start a dummy payment process.
        """
        # Simulate processing delay
        if self.processing_delay > 0:
            time.sleep(self.processing_delay)
        
        # Determine if payment should succeed based on success rate
        should_succeed = random.randint(0, 100) <= self.success_rate
        
        # Generate fake payment ID
        payment_id = f"dummy_{int(timezone.now().timestamp())}_{order.id}"
        
        if not should_succeed:
            return PaymentInitResult(
                success=False,
                error_message="Dummy payment failed (simulated failure)"
            )
        
        # For dummy provider, we'll redirect to a success page with payment data
        # In a real provider, this would redirect to the provider's payment page
        redirect_url = f"{return_url}?payment_id={payment_id}&status=success&order_id={order.id}"
        
        return PaymentInitResult(
            redirect_url=redirect_url,
            success=True
        )
    
    def handle_webhook(self, request: HttpRequest) -> PaymentWebhookResult:
        """
        Handle dummy webhook notifications.
        """
        try:
            # For dummy provider, we'll simulate webhook data
            # In a real provider, you'd parse the actual webhook payload
            
            if request.method == 'GET':
                # Handle return URL (redirect after payment)
                payment_id = request.GET.get('payment_id', '')
                status = request.GET.get('status', 'pending')
                order_id = request.GET.get('order_id', '')
            else:
                # Handle POST webhook
                data = json.loads(request.body.decode('utf-8'))
                payment_id = data.get('payment_id', '')
                status = data.get('status', 'pending')
                order_id = data.get('order_id', '')
            
            # Map dummy status to standard status
            status_mapping = {
                'success': 'completed',
                'completed': 'completed',
                'failed': 'failed',
                'pending': 'pending',
                'canceled': 'canceled'
            }
            
            mapped_status = status_mapping.get(status, 'pending')
            
            return PaymentWebhookResult(
                order_id=order_id,
                payment_id=payment_id,
                status=mapped_status,
                transaction_id=f"txn_{payment_id}",
                success=True,
                raw_data={
                    'dummy_payment_id': payment_id,
                    'dummy_status': status,
                    'dummy_order_id': order_id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        
        except Exception as e:
            return PaymentWebhookResult(
                success=False,
                error_message=f"Failed to process dummy webhook: {str(e)}"
            )
    
    def capture(self, order, amount=None, **kwargs) -> PaymentOperationResult:
        """
        Capture a dummy payment.
        """
        # Simulate processing delay
        if self.processing_delay > 0:
            time.sleep(self.processing_delay)
        
        capture_amount = amount or order.grand_total
        
        # Simulate success/failure
        should_succeed = random.randint(0, 100) <= self.success_rate
        
        if not should_succeed:
            return PaymentOperationResult(
                success=False,
                error_message="Dummy capture failed (simulated failure)"
            )
        
        transaction_id = f"capture_{int(timezone.now().timestamp())}_{order.id}"
        
        return PaymentOperationResult(
            success=True,
            transaction_id=transaction_id,
            amount=capture_amount,
            currency=order.currency,
            raw_response={
                'dummy_capture_id': transaction_id,
                'dummy_amount': str(capture_amount),
                'dummy_currency': order.currency,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def refund(self, order, amount=None, reason='', **kwargs) -> PaymentOperationResult:
        """
        Refund a dummy payment.
        """
        # Simulate processing delay
        if self.processing_delay > 0:
            time.sleep(self.processing_delay)
        
        refund_amount = amount or order.grand_total
        
        # Simulate success/failure
        should_succeed = random.randint(0, 100) <= self.success_rate
        
        if not should_succeed:
            return PaymentOperationResult(
                success=False,
                error_message="Dummy refund failed (simulated failure)"
            )
        
        transaction_id = f"refund_{int(timezone.now().timestamp())}_{order.id}"
        
        return PaymentOperationResult(
            success=True,
            transaction_id=transaction_id,
            amount=refund_amount,
            currency=order.currency,
            raw_response={
                'dummy_refund_id': transaction_id,
                'dummy_amount': str(refund_amount),
                'dummy_currency': order.currency,
                'dummy_reason': reason,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def get_payment_status(self, payment_id: str) -> PaymentWebhookResult:
        """
        Get dummy payment status.
        """
        # For dummy provider, always return completed status
        return PaymentWebhookResult(
            payment_id=payment_id,
            status='completed',
            transaction_id=f"status_{payment_id}",
            success=True,
            raw_data={
                'dummy_payment_id': payment_id,
                'dummy_status': 'completed',
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def validate_webhook_signature(self, request: HttpRequest) -> bool:
        """
        Validate dummy webhook signature.
        """
        # For dummy provider, always return True
        # In a real provider, you'd validate the actual signature
        return True