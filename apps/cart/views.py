"""
Views for cart app.
"""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.catalog.models import Product
from .services import CartService


class CartDetailView(TemplateView):
    """
    View for displaying cart contents.
    """
    template_name = 'cart/cart_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cart_service = CartService(
            user=self.request.user,
            session=self.request.session
        )
        
        context['cart_summary'] = cart_service.get_cart_summary()
        return context


class AddToCartView(View):
    """
    View for adding products to cart.
    """
    
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
            return redirect(product.get_absolute_url())
        
        cart_service = CartService(
            user=request.user,
            session=request.session
        )
        
        try:
            cart_service.add_product(product, quantity)
            messages.success(
                request,
                f'{product.name} ha sido añadido al carrito.'
            )
        except ValueError as e:
            messages.error(request, str(e))
        
        # Return JSON response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            cart_summary = cart_service.get_cart_summary()
            return JsonResponse({
                'success': True,
                'cart_total_items': cart_summary['total_items'],
                'message': f'{product.name} ha sido añadido al carrito.'
            })
        
        # Redirect to cart or product page
        next_url = request.POST.get('next', reverse('cart:cart_detail'))
        return redirect(next_url)


class UpdateCartItemView(View):
    """
    View for updating cart item quantities.
    """
    
    def post(self, request, item_id):
        quantity = int(request.POST.get('quantity', 0))
        
        cart_service = CartService(
            user=request.user,
            session=request.session
        )
        
        try:
            # Get the cart item to find the product
            cart = cart_service.get_cart()
            cart_item = cart.items.get(id=item_id)
            product = cart_item.product
            
            if quantity <= 0:
                cart_service.remove_product(product)
                messages.success(request, f'{product.name} ha sido eliminado del carrito.')
            else:
                cart_service.update_quantity(product, quantity)
                messages.success(request, f'Cantidad de {product.name} actualizada.')
        
        except Exception as e:
            messages.error(request, 'Error al actualizar el carrito.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            cart_summary = cart_service.get_cart_summary()
            return JsonResponse({
                'success': True,
                'cart_total_items': cart_summary['total_items'],
                'cart_subtotal': float(cart_summary['subtotal']),
            })
        
        return redirect('cart:cart_detail')


class RemoveFromCartView(View):
    """
    View for removing products from cart.
    """
    
    def post(self, request, item_id):
        cart_service = CartService(
            user=request.user,
            session=request.session
        )
        
        try:
            # Get the cart item to find the product
            cart = cart_service.get_cart()
            cart_item = cart.items.get(id=item_id)
            product = cart_item.product
            
            cart_service.remove_product(product)
            messages.success(request, f'{product.name} ha sido eliminado del carrito.')
        
        except Exception as e:
            messages.error(request, 'Error al eliminar el producto del carrito.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            cart_summary = cart_service.get_cart_summary()
            return JsonResponse({
                'success': True,
                'cart_total_items': cart_summary['total_items'],
                'cart_subtotal': float(cart_summary['subtotal']),
            })
        
        return redirect('cart:cart_detail')


class ClearCartView(View):
    """
    View for clearing the entire cart.
    """
    
    def post(self, request):
        cart_service = CartService(
            user=request.user,
            session=request.session
        )
        
        cart_service.clear_cart()
        messages.success(request, 'El carrito ha sido vaciado.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'cart_total_items': 0,
                'cart_subtotal': 0,
            })
        
        return redirect('cart:cart_detail')