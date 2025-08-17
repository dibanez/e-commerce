"""
Views for orders app.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView

from apps.cart.services import CartService
from .forms import CheckoutForm
from .models import Order
from .services import OrderService


class CheckoutView(FormView):
    """
    Checkout view for creating orders.
    """
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm
    
    def dispatch(self, request, *args, **kwargs):
        # Check if cart is not empty
        cart_service = CartService(user=request.user, session=request.session)
        cart_summary = cart_service.get_cart_summary()
        
        if cart_summary['is_empty']:
            messages.warning(request, 'Tu carrito está vacío.')
            return redirect('cart:cart_detail')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add cart summary to context
        cart_service = CartService(user=self.request.user, session=self.request.session)
        context['cart_summary'] = cart_service.get_cart_summary()
        
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Pre-fill guest email if user is not authenticated
        if not self.request.user.is_authenticated:
            initial['guest_email'] = ''
        
        # Pre-fill user data if available
        if self.request.user.is_authenticated:
            user = self.request.user
            initial.update({
                'billing_first_name': user.first_name,
                'billing_last_name': user.last_name,
            })
            
            # Try to get default addresses
            try:
                billing_address = user.addresses.filter(type='billing', is_default=True).first()
                if billing_address:
                    initial.update({
                        'billing_first_name': billing_address.first_name,
                        'billing_last_name': billing_address.last_name,
                        'billing_company': billing_address.company,
                        'billing_address_line_1': billing_address.address_line_1,
                        'billing_address_line_2': billing_address.address_line_2,
                        'billing_city': billing_address.city,
                        'billing_state': billing_address.state,
                        'billing_postal_code': billing_address.postal_code,
                        'billing_country': billing_address.country,
                        'billing_phone': billing_address.phone,
                    })
                
                shipping_address = user.addresses.filter(type='shipping', is_default=True).first()
                if shipping_address:
                    initial.update({
                        'shipping_first_name': shipping_address.first_name,
                        'shipping_last_name': shipping_address.last_name,
                        'shipping_company': shipping_address.company,
                        'shipping_address_line_1': shipping_address.address_line_1,
                        'shipping_address_line_2': shipping_address.address_line_2,
                        'shipping_city': shipping_address.city,
                        'shipping_state': shipping_address.state,
                        'shipping_postal_code': shipping_address.postal_code,
                        'shipping_country': shipping_address.country,
                        'shipping_phone': shipping_address.phone,
                        'shipping_same_as_billing': False,
                    })
            except Exception:
                pass  # Ignore errors getting addresses
        
        return initial
    
    def form_valid(self, form):
        try:
            # Create order
            order = OrderService.checkout_flow(
                user=self.request.user if self.request.user.is_authenticated else None,
                session=self.request.session,
                billing_data=form.get_billing_data(),
                shipping_data=form.get_shipping_data(),
                additional_data=form.get_additional_data()
            )
            
            messages.success(
                self.request,
                f'Pedido {order.number} creado correctamente. Procede al pago.'
            )
            
            # Redirect to payment selection
            return redirect('payments:payment_methods', order_number=order.number)
        
        except ValueError as e:
            messages.error(self.request, f'Error al crear el pedido: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrige los errores en el formulario.'
        )
        return super().form_invalid(form)


class OrderDetailView(DetailView):
    """
    View for displaying order details.
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'number'
    slug_url_kwarg = 'number'
    
    def get_queryset(self):
        queryset = Order.objects.select_related().prefetch_related('items__product')
        
        # If user is authenticated, only show their orders
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        
        # For anonymous users, we'll check session or require email verification
        return queryset
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Additional security check for anonymous users
        if not self.request.user.is_authenticated:
            # You could implement email verification here
            # For now, we'll allow access to any order by number
            pass
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_summary'] = OrderService.get_order_summary(self.object)
        return context


class OrderListView(LoginRequiredMixin, ListView):
    """
    View for listing user's orders.
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).exclude(status='draft').order_by('-created_at')


class OrderCancelView(LoginRequiredMixin, DetailView):
    """
    View for canceling orders.
    """
    model = Order
    slug_field = 'number'
    slug_url_kwarg = 'number'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        
        try:
            OrderService.cancel_order(order, reason='Canceled by customer')
            messages.success(
                request,
                f'Pedido {order.number} ha sido cancelado correctamente.'
            )
        except ValueError as e:
            messages.error(request, f'Error al cancelar el pedido: {str(e)}')
        
        return redirect('orders:order_detail', number=order.number)