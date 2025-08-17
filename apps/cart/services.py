"""
Cart service layer for business logic.
"""
from decimal import Decimal
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from typing import Optional

from apps.catalog.models import Product
from .models import Cart, CartItem


class CartService:
    """
    Service class for cart operations.
    """
    
    def __init__(self, user=None, session: Optional[SessionBase] = None):
        self.user = user
        self.session = session
        self._cart = None

    def get_cart(self) -> Cart:
        """
        Get or create a cart for the current user/session.
        """
        if self._cart:
            return self._cart

        if self.user and self.user.is_authenticated:
            # Try to get user's cart
            cart, created = Cart.objects.get_or_create(user=self.user)
            
            # If user was anonymous and now logged in, merge session cart
            if created and self.session:
                session_cart = self._get_session_cart()
                if session_cart:
                    cart.merge_with(session_cart)
        else:
            # Anonymous user - use session cart
            cart = self._get_or_create_session_cart()

        self._cart = cart
        return cart

    def _get_session_cart(self) -> Optional[Cart]:
        """
        Get cart for current session.
        """
        if not self.session or not hasattr(self.session, 'session_key'):
            return None
        
        try:
            return Cart.objects.get(session_key=self.session.session_key)
        except Cart.DoesNotExist:
            return None

    def _get_or_create_session_cart(self) -> Cart:
        """
        Get or create cart for current session.
        """
        if not self.session:
            raise ValueError("Session is required for anonymous cart")
        
        # Ensure session is saved to get a session key
        if not self.session.session_key:
            self.session.save()
        
        cart, created = Cart.objects.get_or_create(
            session_key=self.session.session_key
        )
        return cart

    def add_product(self, product: Product, quantity: int = 1) -> CartItem:
        """
        Add a product to the cart.
        """
        if not product.is_active:
            raise ValueError("Product is not active")
        
        if not product.is_in_stock and not product.allow_backorders:
            raise ValueError("Product is out of stock")
        
        cart = self.get_cart()
        return cart.add_item(product, quantity)

    def remove_product(self, product: Product) -> None:
        """
        Remove a product from the cart.
        """
        cart = self.get_cart()
        cart.remove_item(product)

    def update_quantity(self, product: Product, quantity: int) -> None:
        """
        Update the quantity of a product in the cart.
        """
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        cart = self.get_cart()
        cart.update_item_quantity(product, quantity)

    def clear_cart(self) -> None:
        """
        Clear all items from the cart.
        """
        cart = self.get_cart()
        cart.clear()

    def get_cart_summary(self) -> dict:
        """
        Get cart summary with totals.
        """
        cart = self.get_cart()
        
        return {
            'total_items': cart.total_items,
            'subtotal': cart.subtotal,
            'is_empty': cart.is_empty,
            'items': list(cart.items.select_related('product')),
        }

    def migrate_to_user(self, user) -> None:
        """
        Migrate session cart to user cart after login.
        """
        if not user or not user.is_authenticated:
            return
        
        session_cart = self._get_session_cart()
        if not session_cart:
            return
        
        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(user=user)
        
        # Merge session cart into user cart
        if not created:
            user_cart.merge_with(session_cart)
        else:
            # Transfer session cart to user
            session_cart.user = user
            session_cart.session_key = None
            session_cart.save()
        
        self._cart = None  # Reset cached cart