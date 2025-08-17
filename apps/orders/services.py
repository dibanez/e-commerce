"""
Order service layer for business logic.
"""
from decimal import Decimal
from django.db import transaction
from typing import Dict, Any, Optional

from apps.cart.models import Cart
from apps.cart.services import CartService
from .models import Order, OrderItem


class OrderService:
    """
    Service class for order operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        cart: Cart,
        billing_data: Dict[str, Any],
        shipping_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        Create an order from cart data.
        """
        if cart.is_empty:
            raise ValueError("Cannot create order from empty cart")
        
        additional_data = additional_data or {}
        
        # Create order
        order = Order(
            user=cart.user,
            guest_email=additional_data.get('guest_email'),
            currency=additional_data.get('currency', 'EUR'),
            
            # Billing information
            billing_first_name=billing_data['first_name'],
            billing_last_name=billing_data['last_name'],
            billing_company=billing_data.get('company', ''),
            billing_address_line_1=billing_data['address_line_1'],
            billing_address_line_2=billing_data.get('address_line_2', ''),
            billing_city=billing_data['city'],
            billing_state=billing_data['state'],
            billing_postal_code=billing_data['postal_code'],
            billing_country=billing_data.get('country', 'ES'),
            billing_phone=billing_data.get('phone', ''),
            
            # Shipping information
            shipping_first_name=shipping_data['first_name'],
            shipping_last_name=shipping_data['last_name'],
            shipping_company=shipping_data.get('company', ''),
            shipping_address_line_1=shipping_data['address_line_1'],
            shipping_address_line_2=shipping_data.get('address_line_2', ''),
            shipping_city=shipping_data['city'],
            shipping_state=shipping_data['state'],
            shipping_postal_code=shipping_data['postal_code'],
            shipping_country=shipping_data.get('country', 'ES'),
            shipping_phone=shipping_data.get('phone', ''),
            
            # Additional data
            notes=additional_data.get('notes', ''),
            terms_accepted=additional_data.get('terms_accepted', False),
            newsletter_signup=additional_data.get('newsletter_signup', False),
        )
        
        order.save()
        
        # Create order items from cart items
        for cart_item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                product_description=cart_item.product.short_description or cart_item.product.description,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                line_total=cart_item.total_price,
            )
        
        # Calculate totals
        order.calculate_totals()
        order.save()
        
        return order
    
    @staticmethod
    def validate_order_data(billing_data: Dict[str, Any], shipping_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate order data and return any errors.
        """
        errors = {}
        
        # Required billing fields
        required_billing_fields = [
            'first_name', 'last_name', 'address_line_1', 'city', 'state', 'postal_code'
        ]
        
        for field in required_billing_fields:
            if not billing_data.get(field):
                errors[f'billing_{field}'] = f'Este campo es obligatorio'
        
        # Required shipping fields
        required_shipping_fields = [
            'first_name', 'last_name', 'address_line_1', 'city', 'state', 'postal_code'
        ]
        
        for field in required_shipping_fields:
            if not shipping_data.get(field):
                errors[f'shipping_{field}'] = f'Este campo es obligatorio'
        
        return errors
    
    @staticmethod
    def get_order_summary(order: Order) -> Dict[str, Any]:
        """
        Get comprehensive order summary.
        """
        items = order.items.select_related('product').all()
        
        return {
            'order': order,
            'items': items,
            'subtotal': order.subtotal,
            'tax_total': order.tax_total,
            'shipping_total': order.shipping_total,
            'discount_total': order.discount_total,
            'grand_total': order.grand_total,
            'total_items': sum(item.quantity for item in items),
            'can_be_canceled': order.status in ['draft', 'pending_payment', 'paid'],
            'can_be_paid': order.status == 'pending_payment',
        }
    
    @staticmethod
    @transaction.atomic
    def process_payment_success(order: Order, payment_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Process successful payment for an order.
        """
        if order.status != 'pending_payment':
            raise ValueError(f"Order {order.number} is not in pending_payment status")
        
        # Mark order as paid
        order.mark_as_paid()
        order.save()
        
        # Optionally update stock quantities
        for item in order.items.select_related('product'):
            if item.product.track_inventory:
                if item.product.stock_quantity >= item.quantity:
                    item.product.stock_quantity -= item.quantity
                    item.product.save(update_fields=['stock_quantity'])
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order, reason: str = '') -> None:
        """
        Cancel an order and restore stock if necessary.
        """
        if order.status not in ['draft', 'pending_payment', 'paid', 'processing']:
            raise ValueError(f"Order {order.number} cannot be canceled from status {order.status}")
        
        # Restore stock if order was paid
        if order.status in ['paid', 'processing']:
            for item in order.items.select_related('product'):
                if item.product.track_inventory:
                    item.product.stock_quantity += item.quantity
                    item.product.save(update_fields=['stock_quantity'])
        
        # Cancel the order
        order.cancel()
        order.save()
    
    @staticmethod
    def checkout_flow(
        user,
        session,
        billing_data: Dict[str, Any],
        shipping_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        Complete checkout flow: validate, create order, clear cart.
        """
        # Validate data
        errors = OrderService.validate_order_data(billing_data, shipping_data)
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        # Get cart
        cart_service = CartService(user=user, session=session)
        cart = cart_service.get_cart()
        
        if cart.is_empty:
            raise ValueError("Cart is empty")
        
        # Create order
        order = OrderService.create_order_from_cart(
            cart=cart,
            billing_data=billing_data,
            shipping_data=shipping_data,
            additional_data=additional_data
        )
        
        # Submit order for payment
        order.submit()
        order.save()
        
        # Clear cart after successful order creation
        cart_service.clear_cart()
        
        return order