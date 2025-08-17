"""
Views for payments app.
"""
import logging
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from apps.orders.models import Order
from .services import PaymentService

logger = logging.getLogger(__name__)


class PaymentMethodSelectionView(TemplateView):
    """
    View for selecting payment method.
    """
    template_name = 'payments/payment_methods.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        order_number = kwargs.get('order_number')
        order = get_object_or_404(Order, number=order_number)
        
        # Check if order can be paid
        if order.status != 'pending_payment':
            messages.error(
                self.request,
                f'El pedido {order.number} no está disponible para pago.'
            )
            return context
        
        context['order'] = order
        context['payment_methods'] = PaymentService.get_available_payment_methods()
        
        return context


class InitiatePaymentView(View):
    """
    View for initiating payment with selected provider.
    """
    
    def post(self, request, order_number):
        order = get_object_or_404(Order, number=order_number)
        provider_code = request.POST.get('provider')
        
        if not provider_code:
            messages.error(request, 'Debe seleccionar un método de pago.')
            return redirect('payments:payment_methods', order_number=order.number)
        
        if order.status != 'pending_payment':
            messages.error(
                request,
                f'El pedido {order.number} no está disponible para pago.'
            )
            return redirect('orders:order_detail', number=order.number)
        
        # Build URLs
        return_url = request.build_absolute_uri(
            reverse('payments:payment_return', kwargs={
                'order_number': order.number,
                'provider_code': provider_code
            })
        )
        notify_url = request.build_absolute_uri(
            reverse('payments:payment_webhook', kwargs={
                'provider_code': provider_code
            })
        )
        
        try:
            result = PaymentService.initiate_payment(
                order=order,
                provider_code=provider_code,
                return_url=return_url,
                notify_url=notify_url
            )
            
            if not result['success']:
                messages.error(
                    request,
                    f'Error al iniciar el pago: {result["error"]}'
                )
                return redirect('payments:payment_methods', order_number=order.number)
            
            # Redirect to payment provider or success page
            if result.get('redirect_url'):
                return redirect(result['redirect_url'])
            
            # If no redirect URL, show success page
            messages.success(request, 'Pago procesado correctamente.')
            return redirect('orders:order_detail', number=order.number)
        
        except Exception as e:
            logger.error(f"Payment initiation error: {e}")
            messages.error(request, f'Error al procesar el pago: {str(e)}')
            return redirect('payments:payment_methods', order_number=order.number)


class PaymentReturnView(View):
    """
    View for handling payment returns from providers.
    """
    
    def get(self, request, order_number, provider_code):
        """
        Handle payment return (success/cancel redirect).
        """
        order = get_object_or_404(Order, number=order_number)
        
        try:
            # Process the return as a webhook
            result = PaymentService.process_webhook(provider_code, request)
            
            if result['success']:
                messages.success(
                    request,
                    f'Pago completado correctamente para el pedido {order.number}.'
                )
            else:
                messages.error(
                    request,
                    f'Error en el pago: {result.get("error", "Error desconocido")}'
                )
        
        except Exception as e:
            logger.error(f"Payment return processing error: {e}")
            messages.error(request, 'Error al procesar el resultado del pago.')
        
        return redirect('orders:order_detail', number=order.number)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    """
    View for handling payment webhooks from providers.
    """
    
    def post(self, request, provider_code):
        """
        Handle webhook notifications from payment providers.
        """
        try:
            result = PaymentService.process_webhook(provider_code, request)
            
            if result['success']:
                logger.info(f"Webhook processed successfully for provider {provider_code}")
                return HttpResponse('OK', status=200)
            else:
                logger.error(f"Webhook processing failed: {result.get('error')}")
                return HttpResponse('Error', status=400)
        
        except Exception as e:
            logger.error(f"Webhook processing exception: {e}")
            return HttpResponse('Error', status=500)
    
    def get(self, request, provider_code):
        """
        Handle GET webhooks (for providers that use GET for notifications).
        """
        return self.post(request, provider_code)


class PaymentStatusView(View):
    """
    View for checking payment status.
    """
    
    def get(self, request, payment_id):
        """
        Get payment status via AJAX.
        """
        from .models import Payment
        
        try:
            payment = Payment.objects.get(id=payment_id)
            result = PaymentService.get_payment_status(payment)
            
            return JsonResponse({
                'success': result['success'],
                'status': payment.status,
                'provider_status': result.get('status'),
                'error': result.get('error')
            })
        
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Payment not found'
            }, status=404)
        
        except Exception as e:
            logger.error(f"Payment status check error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PaymentSuccessView(TemplateView):
    """
    View for displaying payment success page.
    """
    template_name = 'payments/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        order_number = kwargs.get('order_number')
        if order_number:
            context['order'] = get_object_or_404(Order, number=order_number)
        
        return context


class PaymentFailureView(TemplateView):
    """
    View for displaying payment failure page.
    """
    template_name = 'payments/payment_failure.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        order_number = kwargs.get('order_number')
        if order_number:
            context['order'] = get_object_or_404(Order, number=order_number)
        
        context['error_message'] = self.request.GET.get('error', '')
        
        return context