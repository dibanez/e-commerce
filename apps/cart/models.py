"""
Cart models for the ecommerce application.
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Product


class Cart(models.Model):
    """
    Shopping cart model that supports both session-based and user-based carts.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        verbose_name='user'
    )
    session_key = models.CharField(
        'session key',
        max_length=40,
        null=True,
        blank=True,
        help_text='Session key for anonymous users'
    )
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'cart'
        verbose_name_plural = 'carts'
        db_table = 'cart_cart'
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='cart_must_have_user_or_session'
            )
        ]

    def __str__(self) -> str:
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Anonymous cart ({self.session_key[:8]}...)"

    @property
    def total_items(self) -> int:
        """
        Get total number of items in the cart.
        """
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self) -> Decimal:
        """
        Get cart subtotal (sum of all item totals).
        """
        total = sum(item.total_price for item in self.items.all())
        return total if total is not None else Decimal('0.00')

    @property
    def is_empty(self) -> bool:
        """
        Check if cart is empty.
        """
        return not self.items.exists()

    def add_item(self, product: Product, quantity: int = 1) -> 'CartItem':
        """
        Add a product to the cart or update quantity if it already exists.
        """
        cart_item, created = self.items.get_or_create(
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': product.base_price
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item

    def remove_item(self, product: Product) -> None:
        """
        Remove a product from the cart.
        """
        self.items.filter(product=product).delete()

    def update_item_quantity(self, product: Product, quantity: int) -> None:
        """
        Update the quantity of a specific item.
        """
        if quantity <= 0:
            self.remove_item(product)
        else:
            cart_item = self.items.get(product=product)
            cart_item.quantity = quantity
            cart_item.save()

    def clear(self) -> None:
        """
        Remove all items from the cart.
        """
        self.items.all().delete()

    def merge_with(self, other_cart: 'Cart') -> None:
        """
        Merge another cart with this one.
        """
        for item in other_cart.items.all():
            self.add_item(item.product, item.quantity)
        
        other_cart.delete()


class CartItem(models.Model):
    """
    Cart item model representing a product in a cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='cart'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='product'
    )
    quantity = models.PositiveIntegerField(
        'quantity',
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        'unit price',
        max_digits=10,
        decimal_places=2,
        help_text='Price at the time item was added to cart'
    )
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'cart item'
        verbose_name_plural = 'cart items'
        db_table = 'cart_cartitem'
        unique_together = [['cart', 'product']]
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    @property
    def total_price(self) -> Decimal:
        """
        Get total price for this cart item (quantity * unit_price).
        """
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs) -> None:
        # Update the cart's updated_at timestamp
        if self.cart_id:
            Cart.objects.filter(pk=self.cart_id).update(updated_at=models.functions.Now())
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        # Update the cart's updated_at timestamp
        if self.cart_id:
            Cart.objects.filter(pk=self.cart_id).update(updated_at=models.functions.Now())
        super().delete(*args, **kwargs)