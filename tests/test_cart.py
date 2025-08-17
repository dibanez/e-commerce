"""
Tests for cart app.
"""
import pytest
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware

from apps.cart.models import Cart, CartItem
from apps.cart.services import CartService
from apps.catalog.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestCartModel:
    """Test Cart model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=10,
            is_active=True
        )

    def test_create_cart_for_user(self):
        """Test creating a cart for authenticated user."""
        cart = Cart.objects.create(user=self.user)
        
        assert cart.user == self.user
        assert cart.session_key is None
        assert str(cart) == f"Cart for {self.user.email}"

    def test_create_cart_for_session(self):
        """Test creating a cart for anonymous user."""
        session_key = "test-session-key"
        cart = Cart.objects.create(session_key=session_key)
        
        assert cart.user is None
        assert cart.session_key == session_key
        assert str(cart) == f"Anonymous cart ({session_key[:8]}...)"

    def test_cart_total_items(self):
        """Test cart total_items property."""
        cart = Cart.objects.create(user=self.user)
        
        # Initially empty
        assert cart.total_items == 0
        
        # Add items
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.base_price
        )
        
        assert cart.total_items == 2

    def test_cart_is_empty(self):
        """Test cart is_empty property."""
        cart = Cart.objects.create(user=self.user)
        
        # Initially empty
        assert cart.is_empty is True
        
        # Add item
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            unit_price=self.product.base_price
        )
        
        assert cart.is_empty is False

    def test_cart_subtotal(self):
        """Test cart subtotal calculation."""
        cart = Cart.objects.create(user=self.user)
        
        # Initially zero
        assert cart.subtotal == Decimal("0.00")
        
        # Add item
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.base_price
        )
        
        expected_subtotal = Decimal("2") * self.product.base_price
        assert cart.subtotal == expected_subtotal


@pytest.mark.django_db
class TestCartItemModel:
    """Test CartItem model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=10,
            is_active=True
        )
        
        self.cart = Cart.objects.create(user=self.user)

    def test_create_cart_item(self):
        """Test creating a cart item."""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.base_price
        )
        
        assert cart_item.cart == self.cart
        assert cart_item.product == self.product
        assert cart_item.quantity == 2
        assert cart_item.unit_price == self.product.base_price

    def test_cart_item_total_price(self):
        """Test cart item total_price property."""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3,
            unit_price=self.product.base_price
        )
        
        expected_total = Decimal("3") * self.product.base_price
        assert cart_item.total_price == expected_total

    def test_cart_with_items_properties(self):
        """Test cart properties with items."""
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.base_price
        )
        
        assert self.cart.total_items == 2
        assert self.cart.is_empty is False
        assert self.cart.subtotal == Decimal("2") * self.product.base_price


@pytest.mark.django_db
class TestCartService:
    """Test CartService functionality."""

    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=10,
            is_active=True
        )

    def _get_session(self):
        """Helper to create session."""
        request = self.factory.get("/")
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request.session

    def test_get_cart_for_user(self):
        """Test getting cart for authenticated user."""
        service = CartService(user=self.user)
        cart = service.get_cart()
        
        assert cart.user == self.user
        assert cart.session_key is None

    def test_get_cart_for_anonymous_user(self):
        """Test getting cart for anonymous user."""
        session = self._get_session()
        service = CartService(session=session)
        
        cart = service.get_cart()
        
        assert cart.user is None
        assert cart.session_key == session.session_key

    def test_add_product_to_cart(self):
        """Test adding product to cart."""
        service = CartService(user=self.user)
        cart_item = service.add_product(self.product, quantity=2)
        
        assert cart_item.product == self.product
        assert cart_item.quantity == 2
        assert cart_item.unit_price == self.product.base_price

    def test_add_product_insufficient_stock(self):
        """Test adding product with insufficient stock."""
        # Set product out of stock and no backorders
        self.product.stock_quantity = 0
        self.product.track_inventory = True
        self.product.allow_backorders = False
        self.product.save()
        
        service = CartService(user=self.user)
        
        with pytest.raises(ValueError, match="Product is out of stock"):
            service.add_product(self.product, quantity=1)

    def test_update_cart_item_quantity(self):
        """Test updating cart item quantity."""
        service = CartService(user=self.user)
        
        # Add item first
        service.add_product(self.product, quantity=1)
        
        # Update quantity
        service.update_quantity(self.product, quantity=3)
        
        cart = service.get_cart()
        cart_item = cart.items.get(product=self.product)
        assert cart_item.quantity == 3

    def test_remove_cart_item(self):
        """Test removing cart item."""
        service = CartService(user=self.user)
        
        # Add item first
        service.add_product(self.product, quantity=2)
        cart = service.get_cart()
        assert cart.total_items == 2
        
        # Remove item
        service.remove_product(self.product)
        cart.refresh_from_db()
        assert cart.total_items == 0

    def test_clear_cart(self):
        """Test clearing cart."""
        service = CartService(user=self.user)
        
        # Add items
        service.add_product(self.product, quantity=2)
        cart = service.get_cart()
        assert cart.total_items == 2
        
        # Clear cart
        service.clear_cart()
        cart.refresh_from_db()
        assert cart.total_items == 0

    def test_get_cart_summary(self):
        """Test getting cart summary."""
        service = CartService(user=self.user)
        
        # Add item
        service.add_product(self.product, quantity=2)
        
        summary = service.get_cart_summary()
        
        assert summary["total_items"] == 2
        assert summary["subtotal"] == Decimal("2") * self.product.base_price
        assert summary["is_empty"] is False
        assert len(summary["items"]) == 1
