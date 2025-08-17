"""
Tests for orders app.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.orders.forms import CheckoutForm
from apps.catalog.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestOrderModel:
    """Test Order model functionality."""

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

    def test_create_order(self):
        """Test creating an order."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        assert order.user == self.user
        assert order.billing_first_name == "John"
        assert order.billing_last_name == "Doe"
        assert order.grand_total == Decimal("100.00")
        assert order.number.startswith("ORD-")  # Auto-generated order number
        assert str(order) == f"Order {order.number}"

    def test_order_get_absolute_url(self):
        """Test order absolute URL."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        expected_url = f"/orders/{order.number}/"
        assert order.get_absolute_url() == expected_url

    def test_order_customer_email(self):
        """Test order customer email property."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        assert order.customer_email == self.user.email

    def test_order_customer_name(self):
        """Test order customer name property."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        assert order.customer_name == "John Doe"

    def test_order_billing_address_property(self):
        """Test order formatted billing address."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_company="Test Company",
            billing_address_line_1="123 Test St",
            billing_address_line_2="Apt 4B",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        billing_address = order.billing_address
        assert "John Doe" in billing_address
        assert "Test Company" in billing_address
        assert "123 Test St" in billing_address
        assert "Apt 4B" in billing_address
        assert "Test City, Test State 12345" in billing_address
        assert "ES" in billing_address

    def test_order_shipping_address_property(self):
        """Test order formatted shipping address."""
        order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="Jane",
            shipping_last_name="Smith",
            shipping_company="Shipping Company",
            shipping_address_line_1="456 Ship St",
            shipping_address_line_2="Unit 2A",
            shipping_city="Ship City",
            shipping_state="Ship State",
            shipping_postal_code="67890",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )
        
        shipping_address = order.shipping_address
        assert "Jane Smith" in shipping_address
        assert "Shipping Company" in shipping_address
        assert "456 Ship St" in shipping_address
        assert "Unit 2A" in shipping_address
        assert "Ship City, Ship State 67890" in shipping_address
        assert "ES" in shipping_address


@pytest.mark.django_db
class TestOrderItemModel:
    """Test OrderItem model functionality."""

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
        
        self.order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )

    def test_create_order_item(self):
        """Test creating an order item."""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.base_price
        )
        
        assert order_item.order == self.order
        assert order_item.product == self.product
        assert order_item.quantity == 2
        assert order_item.unit_price == self.product.base_price
        # The actual string uses product_name, not product.name
        expected_str = f"2x {self.product.name} in {self.order.number}"
        assert str(order_item) == expected_str

    def test_order_item_line_total(self):
        """Test order item line total calculation."""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=self.product.base_price
        )
        
        expected_total = Decimal("3") * self.product.base_price
        assert order_item.line_total == expected_total


@pytest.mark.django_db
class TestOrderStatusHistory:
    """Test OrderStatusHistory model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.order = Order.objects.create(
            user=self.user,
            billing_first_name="John",
            billing_last_name="Doe",
            billing_address_line_1="123 Test St",
            billing_city="Test City",
            billing_state="Test State",
            billing_postal_code="12345",
            billing_country="ES",
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address_line_1="123 Test St",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_postal_code="12345",
            shipping_country="ES",
            grand_total=Decimal("100.00"),
            terms_accepted=True
        )

    def test_create_status_history(self):
        """Test creating order status history."""
        history = OrderStatusHistory.objects.create(
            order=self.order,
            from_status="draft",
            to_status="pending_payment",
            reason="Order submitted for payment"
        )
        
        assert history.order == self.order
        assert history.from_status == "draft"
        assert history.to_status == "pending_payment"
        assert history.reason == "Order submitted for payment"
        expected_str = f"{self.order.number}: draft → pending_payment"
        assert str(history) == expected_str


@pytest.mark.django_db
class TestCheckoutForm:
    """Test CheckoutForm functionality."""

    def test_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            "billing_first_name": "John",
            "billing_last_name": "Doe",
            "billing_address_line_1": "123 Test St",
            "billing_city": "Test City",
            "billing_state": "Test State",
            "billing_postal_code": "12345",
            "billing_country": "ES",
            "shipping_same_as_billing": True,
            "terms_accepted": True
        }
        
        form = CheckoutForm(data=form_data)
        assert form.is_valid()

    def test_form_different_shipping_address(self):
        """Test form with different shipping address."""
        form_data = {
            "billing_first_name": "John",
            "billing_last_name": "Doe",
            "billing_address_line_1": "123 Test St",
            "billing_city": "Test City",
            "billing_state": "Test State",
            "billing_postal_code": "12345",
            "billing_country": "ES",
            "shipping_same_as_billing": False,
            "shipping_first_name": "Jane",
            "shipping_last_name": "Smith",
            "shipping_address_line_1": "456 Ship St",
            "shipping_city": "Ship City",
            "shipping_state": "Ship State",
            "shipping_postal_code": "67890",
            "shipping_country": "ES",
            "terms_accepted": True
        }
        
        form = CheckoutForm(data=form_data)
        assert form.is_valid()

    def test_form_get_billing_data(self):
        """Test getting billing data from form."""
        form_data = {
            "billing_first_name": "John",
            "billing_last_name": "Doe",
            "billing_address_line_1": "123 Test St",
            "billing_city": "Test City",
            "billing_state": "Test State",
            "billing_postal_code": "12345",
            "billing_country": "ES",
            "shipping_same_as_billing": True,
            "terms_accepted": True
        }
        
        form = CheckoutForm(data=form_data)
        assert form.is_valid()
        
        billing_data = form.get_billing_data()
        # The form returns keys without "billing_" prefix
        assert billing_data["first_name"] == "John"
        assert billing_data["last_name"] == "Doe"
        assert billing_data["city"] == "Test City"

    def test_form_get_shipping_data(self):
        """Test getting shipping data from form."""
        form_data = {
            "billing_first_name": "John",
            "billing_last_name": "Doe",
            "billing_address_line_1": "123 Test St",
            "billing_city": "Test City",
            "billing_state": "Test State",
            "billing_postal_code": "12345",
            "billing_country": "ES",
            "shipping_same_as_billing": False,
            "shipping_first_name": "Jane",
            "shipping_last_name": "Smith",
            "shipping_address_line_1": "456 Ship St",
            "shipping_city": "Ship City",
            "shipping_state": "Ship State",
            "shipping_postal_code": "67890",
            "shipping_country": "ES",
            "terms_accepted": True
        }
        
        form = CheckoutForm(data=form_data)
        assert form.is_valid()
        
        shipping_data = form.get_shipping_data()
        # The form returns keys without "shipping_" prefix
        assert shipping_data["first_name"] == "Jane"
        assert shipping_data["last_name"] == "Smith"
        assert shipping_data["city"] == "Ship City"
