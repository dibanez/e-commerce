"""
Tests for core app.
"""
import pytest
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.core.views import HomeView, handler404, handler500
from apps.core.context_processors import search
from apps.catalog.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestHomeView:
    """Test HomeView functionality."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test categories
        self.parent_category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )
        
        self.child_category = Category.objects.create(
            name="Laptops",
            slug="laptops",
            parent=self.parent_category,
            is_active=True
        )
        
        # Create test products with correct field names
        self.featured_product = Product.objects.create(
            name="Featured Laptop",
            slug="featured-laptop",
            category=self.child_category,
            sku="FEAT-001",
            base_price=999.99,
            stock_quantity=10,
            is_active=True,
            is_featured=True
        )
        
        self.regular_product = Product.objects.create(
            name="Regular Laptop",
            slug="regular-laptop",
            category=self.child_category,
            sku="REG-001",
            base_price=799.99,
            stock_quantity=5,
            is_active=True,
            is_featured=False
        )

    def test_home_view_get(self):
        """Test GET request to home view."""
        response = self.client.get(reverse("core:home"))
        
        assert response.status_code == 200
        assert "featured_products" in response.context
        assert "main_categories" in response.context

    def test_home_view_featured_products(self):
        """Test that featured products are included in context."""
        response = self.client.get(reverse("core:home"))
        
        featured_products = response.context["featured_products"]
        assert self.featured_product in featured_products
        assert self.regular_product not in featured_products

    def test_home_view_main_categories(self):
        """Test that main categories are included in context."""
        response = self.client.get(reverse("core:home"))
        
        main_categories = response.context["main_categories"]
        assert self.parent_category in main_categories
        assert self.child_category not in main_categories  # Child category should not be in main

    def test_home_view_template_used(self):
        """Test that correct template is used."""
        response = self.client.get(reverse("core:home"))
        
        assert "core/home.html" in [t.name for t in response.templates]

    def test_home_view_with_inactive_products(self):
        """Test that inactive products are not shown."""
        # Create inactive featured product
        inactive_product = Product.objects.create(
            name="Inactive Laptop",
            slug="inactive-laptop",
            category=self.child_category,
            sku="INACT-001",
            base_price=1299.99,
            stock_quantity=3,
            is_active=False,
            is_featured=True
        )
        
        response = self.client.get(reverse("core:home"))
        featured_products = response.context["featured_products"]
        
        assert inactive_product not in featured_products

    def test_home_view_with_inactive_categories(self):
        """Test that inactive categories are not shown."""
        # Create inactive parent category
        inactive_category = Category.objects.create(
            name="Inactive Category",
            slug="inactive-category",
            is_active=False
        )
        
        response = self.client.get(reverse("core:home"))
        main_categories = response.context["main_categories"]
        
        assert inactive_category not in main_categories


@pytest.mark.django_db
class TestErrorHandlers:
    """Test custom error handlers."""

    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()

    def test_handler404(self):
        """Test 404 error handler."""
        request = self.factory.get("/nonexistent-page/")
        response = handler404(request, None)
        
        assert response.status_code == 404

    def test_handler500(self):
        """Test 500 error handler."""
        request = self.factory.get("/")
        response = handler500(request)
        
        assert response.status_code == 500


class TestSearchContextProcessor:
    """Test search context processor."""

    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()

    def test_search_with_query(self):
        """Test search context processor with query parameter."""
        request = self.factory.get("/?q=laptop")
        context = search(request)
        
        assert context["search_query"] == "laptop"

    def test_search_without_query(self):
        """Test search context processor without query parameter."""
        request = self.factory.get("/")
        context = search(request)
        
        assert context["search_query"] == ""

    def test_search_with_empty_query(self):
        """Test search context processor with empty query parameter."""
        request = self.factory.get("/?q=")
        context = search(request)
        
        assert context["search_query"] == ""

    def test_search_with_multiple_params(self):
        """Test search context processor with multiple parameters."""
        request = self.factory.get("/?q=laptop&category=electronics")
        context = search(request)
        
        assert context["search_query"] == "laptop"


@pytest.mark.django_db
class TestCoreURLs:
    """Test core URL patterns."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()

    def test_home_url_resolves(self):
        """Test that home URL resolves correctly."""
        url = reverse("core:home")
        assert url == "/"

    def test_home_url_accessible(self):
        """Test that home URL is accessible."""
        response = self.client.get("/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestCoreIntegration:
    """Test core app integration with other apps."""

    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        # Create comprehensive test data
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            sku="TEST-001",
            base_price=99.99,
            stock_quantity=10,
            is_active=True,
            is_featured=True
        )

    def test_home_view_with_authenticated_user(self):
        """Test home view with authenticated user."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:home"))
        
        assert response.status_code == 200
        assert response.context["user"].is_authenticated

    def test_home_view_with_anonymous_user(self):
        """Test home view with anonymous user."""
        response = self.client.get(reverse("core:home"))
        
        assert response.status_code == 200
        assert not response.context["user"].is_authenticated

    def test_search_query_in_context(self):
        """Test that search query is available in template context."""
        response = self.client.get("/?q=test")
        
        # The search context processor should add search_query to context
        assert "search_query" in response.context
        assert response.context["search_query"] == "test"
