"""
Tests for payments app.
"""
import pytest
from decimal import Decimal
from django.test import TestCase, RequestFactory
from unittest.mock import Mock

from apps.payments.providers.dummy import DummyProvider
from apps.payments.registry import PaymentProviderRegistry
from apps.orders.models import Order
from apps.users.models import User


@pytest.mark.django_db
class TestDummyProvider:
    """Test DummyProvider functionality."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            billing_first_name='John',
            billing_last_name='Doe',
            billing_address_line_1='123 Test St',
            billing_city='Test City',
            billing_state='Test State',
            billing_postal_code='12345',
            billing_country='ES',
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_address_line_1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='ES',
            grand_total=Decimal('100.00'),
            terms_accepted=True
        )
        
        self.provider = DummyProvider()
        self.factory = RequestFactory()

    def test_provider_attributes(self):
        """Test provider has correct attributes."""
        assert self.provider.code == 'dummy'
        assert self.provider.display_name == 'Dummy Payment (Development)'
        assert self.provider.supports_capture
        assert self.provider.supports_refund

    def test_start_payment_success(self):
        """Test successful payment initiation."""
        result = self.provider.start_payment(
            order=self.order,
            return_url='http://example.com/return/',
            notify_url='http://example.com/notify/'
        )
        
        assert result.success
        assert result.redirect_url
        assert 'payment_id=dummy_' in result.redirect_url

    def test_start_payment_with_low_success_rate(self):
        """Test payment failure with low success rate."""
        provider = DummyProvider(config={'success_rate': 0})
        
        result = provider.start_payment(
            order=self.order,
            return_url='http://example.com/return/',
            notify_url='http://example.com/notify/'
        )
        
        assert not result.success
        assert result.error_message

    def test_handle_webhook_get(self):
        """Test webhook handling with GET request."""
        request = self.factory.get('/webhook/', {
            'payment_id': 'dummy_12345',
            'status': 'success',
            'order_id': str(self.order.id)
        })
        
        result = self.provider.handle_webhook(request)
        
        assert result.success
        assert result.payment_id == 'dummy_12345'
        assert result.status == 'completed'
        assert result.order_id == str(self.order.id)

    def test_capture_payment(self):
        """Test payment capture."""
        result = self.provider.capture(
            order=self.order,
            amount=Decimal('50.00')
        )
        
        assert result.success
        assert result.amount == Decimal('50.00')
        assert result.transaction_id
        assert 'capture_' in result.transaction_id

    def test_refund_payment(self):
        """Test payment refund."""
        result = self.provider.refund(
            order=self.order,
            amount=Decimal('25.00'),
            reason='Customer request'
        )
        
        assert result.success
        assert result.amount == Decimal('25.00')
        assert result.transaction_id
        assert 'refund_' in result.transaction_id


class TestPaymentProviderRegistry:
    """Test PaymentProviderRegistry functionality."""

    def setup_method(self):
        """Set up test registry."""
        self.registry = PaymentProviderRegistry()

    def test_register_provider_manually(self):
        """Test manual provider registration."""
        self.registry.register_provider(DummyProvider)
        
        assert self.registry.is_provider_available('dummy')
        provider = self.registry.get_provider('dummy')
        assert isinstance(provider, DummyProvider)

    def test_get_nonexistent_provider(self):
        """Test getting non-existent provider."""
        provider = self.registry.get_provider('nonexistent')
        assert provider is None

    def test_get_available_providers(self):
        """Test getting all available providers."""
        self.registry.register_provider(DummyProvider)
        
        providers = self.registry.get_available_providers()
        assert len(providers) == 1
        assert isinstance(providers[0], DummyProvider)