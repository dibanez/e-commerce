"""
Payment service layer for business logic.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.urls import reverse
from typing import Dict, List, Optional

from apps.orders.models import Order
from apps.orders.services import OrderService
from .models import Payment, Transaction
from .registry import get_provider, get_available_providers

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service class for payment operations.
    """
    
    @staticmethod
    def get_available_payment_methods() -> List[Dict]:
        """
        Get list of available payment methods.
        """
        providers = get_available_providers()
        methods = []
        
        for provider in providers:
            methods.append({
                'code': provider.code,
                'name': provider.display_name,
                'description': provider.description,
                'test_mode': provider.test_mode,
            })
        
        return methods
    
    @staticmethod
    @transaction.atomic
    def initiate_payment(
        order: Order,
        provider_code: str,
        return_url: str,
        notify_url: str,
        **kwargs
    ) -> Dict:
        """
        Initiate a payment for an order.
        """
        if order.status != 'pending_payment':
            raise ValueError(f"Order {order.number} is not ready for payment")
        
        # Get payment provider
        provider = get_provider(provider_code)
        if not provider:
            raise ValueError(f"Payment provider {provider_code} not available")
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            provider_code=provider_code,
            amount=order.grand_total,
            currency=order.currency,
            status='pending'
        )
        
        try:
            # Start payment with provider
            result = provider.start_payment(
                order=order,
                return_url=return_url,
                notify_url=notify_url,
                **kwargs
            )
            
            # Create transaction record
            Transaction.create_transaction(
                payment=payment,
                transaction_type='authorize',
                amount=order.grand_total,
                success=result.success,
                error_message=result.error_message or '',
                raw_request=kwargs,
                raw_response=result.__dict__
            )
            
            if not result.success:
                payment.mark_as_failed(result.error_message or 'Unknown error')
                return {
                    'success': False,
                    'error': result.error_message,
                    'payment_id': payment.id
                }
            
            # Update payment with external ID if available
            if hasattr(result, 'payment_id') and result.payment_id:
                payment.external_id = result.payment_id
                payment.save()
            
            return {
                'success': True,
                'payment_id': payment.id,
                'redirect_url': result.redirect_url,
                'form_data': result.form_data,
                'render_data': result.render_data,
            }
        
        except Exception as e:
            logger.error(f"Payment initiation failed for order {order.number}: {e}")
            payment.mark_as_failed(str(e))
            return {
                'success': False,
                'error': str(e),
                'payment_id': payment.id
            }
    
    @staticmethod
    @transaction.atomic
    def process_webhook(provider_code: str, request) -> Dict:
        """
        Process payment webhook notification.
        """
        provider = get_provider(provider_code)
        if not provider:
            raise ValueError(f"Payment provider {provider_code} not available")
        
        # Validate webhook signature
        if not provider.validate_webhook_signature(request):
            logger.warning(f"Invalid webhook signature for provider {provider_code}")
            return {
                'success': False,
                'error': 'Invalid signature'
            }
        
        try:
            # Handle webhook
            result = provider.handle_webhook(request)
            
            if not result.success:
                logger.error(f"Webhook processing failed: {result.error_message}")
                return {
                    'success': False,
                    'error': result.error_message
                }
            
            # Find payment by order ID or payment ID
            payment = None
            if result.payment_id:
                try:
                    payment = Payment.objects.get(external_id=result.payment_id)
                except Payment.DoesNotExist:
                    pass
            
            if not payment and result.order_id:
                try:
                    order = Order.objects.get(id=result.order_id)
                    payment = order.payments.filter(
                        provider_code=provider_code,
                        status__in=['pending', 'authorized']
                    ).first()
                except Order.DoesNotExist:
                    pass
            
            if not payment:
                logger.warning(f"Payment not found for webhook: {result.__dict__}")
                return {
                    'success': False,
                    'error': 'Payment not found'
                }
            
            # Create transaction record
            Transaction.create_transaction(
                payment=payment,
                transaction_type='webhook',
                amount=result.amount,
                external_id=result.transaction_id or '',
                success=True,
                raw_response=result.raw_data
            )
            
            # Update payment status
            if result.status == 'completed':
                payment.mark_as_completed(
                    external_id=result.payment_id or payment.external_id,
                    raw_response=result.raw_data
                )
                # Mark order as paid
                OrderService.process_payment_success(payment.order)
                
            elif result.status == 'failed':
                payment.mark_as_failed(
                    reason=result.error_message or 'Payment failed',
                    raw_response=result.raw_data
                )
            
            elif result.status == 'authorized':
                payment.mark_as_authorized(
                    external_id=result.payment_id or payment.external_id,
                    raw_response=result.raw_data
                )
            
            return {
                'success': True,
                'payment_id': payment.id,
                'status': result.status
            }
        
        except Exception as e:
            logger.error(f"Webhook processing error for provider {provider_code}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def capture_payment(payment: Payment, amount: Optional[Decimal] = None) -> Dict:
        """
        Capture an authorized payment.
        """
        if not payment.can_be_captured:
            raise ValueError(f"Payment {payment.id} cannot be captured")
        
        provider = get_provider(payment.provider_code)
        if not provider:
            raise ValueError(f"Payment provider {payment.provider_code} not available")
        
        try:
            result = provider.capture(
                order=payment.order,
                amount=amount
            )
            
            # Create transaction record
            Transaction.create_transaction(
                payment=payment,
                transaction_type='capture',
                amount=result.amount,
                external_id=result.transaction_id or '',
                success=result.success,
                error_message=result.error_message or '',
                raw_response=result.raw_response
            )
            
            if result.success:
                payment.mark_as_captured(raw_response=result.raw_response)
                # Mark order as paid if not already
                if payment.order.status != 'paid':
                    OrderService.process_payment_success(payment.order)
            
            return {
                'success': result.success,
                'error': result.error_message,
                'transaction_id': result.transaction_id,
                'amount': result.amount
            }
        
        except Exception as e:
            logger.error(f"Payment capture failed for payment {payment.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def refund_payment(
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: str = ''
    ) -> Dict:
        """
        Refund a payment.
        """
        if not payment.can_be_refunded:
            raise ValueError(f"Payment {payment.id} cannot be refunded")
        
        refund_amount = amount or payment.refundable_amount
        
        if refund_amount <= 0:
            raise ValueError("Refund amount must be greater than zero")
        
        if refund_amount > payment.refundable_amount:
            raise ValueError("Refund amount exceeds refundable amount")
        
        provider = get_provider(payment.provider_code)
        if not provider:
            raise ValueError(f"Payment provider {payment.provider_code} not available")
        
        try:
            result = provider.refund(
                order=payment.order,
                amount=refund_amount,
                reason=reason
            )
            
            # Create transaction record
            Transaction.create_transaction(
                payment=payment,
                transaction_type='refund',
                amount=result.amount,
                external_id=result.transaction_id or '',
                success=result.success,
                error_message=result.error_message or '',
                raw_response=result.raw_response
            )
            
            if result.success:
                # Update payment status
                if refund_amount >= payment.amount:
                    payment.status = 'refunded'
                else:
                    payment.status = 'partially_refunded'
                payment.save()
                
                # Update order status if fully refunded
                if payment.status == 'refunded':
                    payment.order.refund()
                    payment.order.save()
            
            return {
                'success': result.success,
                'error': result.error_message,
                'transaction_id': result.transaction_id,
                'amount': result.amount
            }
        
        except Exception as e:
            logger.error(f"Payment refund failed for payment {payment.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_payment_status(payment: Payment) -> Dict:
        """
        Get current payment status from provider.
        """
        provider = get_provider(payment.provider_code)
        if not provider:
            return {
                'success': False,
                'error': f"Payment provider {payment.provider_code} not available"
            }
        
        try:
            result = provider.get_payment_status(payment.external_id)
            
            return {
                'success': result.success,
                'status': result.status,
                'error': result.error_message,
                'raw_data': result.raw_data
            }
        
        except Exception as e:
            logger.error(f"Failed to get payment status for {payment.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }