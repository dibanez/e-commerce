"""
Tests for catalog app.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import (
    Category, Product, ProductAttribute, ProductAttributeOption, 
    ProductAttributeValue, ProductImage
)


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model functionality."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name="Electronics",
            is_active=True
        )
        
        assert category.name == "Electronics"
        assert category.slug == "electronics"  # Auto-generated
        assert category.is_active is True
        assert str(category) == "Electronics"

    def test_category_hierarchy(self):
        """Test category parent-child relationship."""
        parent = Category.objects.create(
            name="Electronics",
            is_active=True
        )
        
        child = Category.objects.create(
            name="Laptops",
            parent=parent,
            is_active=True
        )
        
        assert child.parent == parent
        assert child in parent.children.all()

    def test_category_get_descendants(self):
        """Test getting category descendants."""
        parent = Category.objects.create(name="Electronics")
        child1 = Category.objects.create(name="Laptops", parent=parent)
        child2 = Category.objects.create(name="Phones", parent=parent)
        grandchild = Category.objects.create(name="Gaming Laptops", parent=child1)
        
        descendants = parent.get_descendants()
        
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants
        assert parent not in descendants  # include_self=False by default

    def test_category_get_descendants_include_self(self):
        """Test getting category descendants including self."""
        parent = Category.objects.create(name="Electronics")
        child = Category.objects.create(name="Laptops", parent=parent)
        
        descendants = parent.get_descendants(include_self=True)
        
        assert parent in descendants
        assert child in descendants


@pytest.mark.django_db
class TestProductModel:
    """Test Product model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )

    def test_create_product(self):
        """Test creating a product."""
        product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=10,
            is_active=True
        )
        
        assert product.name == "Test Product"
        assert product.slug == "test-product"  # Auto-generated
        assert product.category == self.category
        assert product.sku == "TEST-001"
        assert product.base_price == Decimal("99.99")
        assert str(product) == "Test Product"

    def test_product_is_in_stock(self):
        """Test product stock checking."""
        # Product with stock and tracking enabled
        product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=10,
            track_inventory=True,
            is_active=True
        )
        
        assert product.is_in_stock is True
        
        # Product out of stock
        product.stock_quantity = 0
        product.save()
        assert product.is_in_stock is False

    def test_product_without_inventory_tracking(self):
        """Test product without inventory tracking."""
        product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            stock_quantity=0,
            track_inventory=False,
            is_active=True
        )
        
        # Should be in stock even with 0 quantity when tracking is disabled
        assert product.is_in_stock is True

    def test_product_formatted_price(self):
        """Test product formatted price property."""
        product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            currency="EUR",
            is_active=True
        )
        
        assert product.formatted_price == "99.99 €"

    def test_product_get_absolute_url(self):
        """Test product absolute URL."""
        product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            is_active=True
        )
        
        expected_url = f"/catalog/product/{product.slug}/"
        assert product.get_absolute_url() == expected_url


@pytest.mark.django_db
class TestProductAttributeModel:
    """Test ProductAttribute model functionality."""

    def test_create_product_attribute(self):
        """Test creating a product attribute."""
        attribute = ProductAttribute.objects.create(
            name="Color",
            code="color",
            type="text"
        )
        
        assert attribute.name == "Color"
        assert attribute.code == "color"
        assert attribute.type == "text"
        assert str(attribute) == "Color"

    def test_product_attribute_types(self):
        """Test different attribute types."""
        text_attr = ProductAttribute.objects.create(
            name="Description", code="desc", type="text"
        )
        integer_attr = ProductAttribute.objects.create(
            name="Count", code="count", type="integer"
        )
        decimal_attr = ProductAttribute.objects.create(
            name="Weight", code="weight", type="decimal"
        )
        boolean_attr = ProductAttribute.objects.create(
            name="Waterproof", code="waterproof", type="boolean"
        )
        
        assert text_attr.type == "text"
        assert integer_attr.type == "integer"
        assert decimal_attr.type == "decimal"
        assert boolean_attr.type == "boolean"


@pytest.mark.django_db
class TestProductAttributeOptionModel:
    """Test ProductAttributeOption model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.attribute = ProductAttribute.objects.create(
            name="Color",
            code="color",
            type="enum"
        )

    def test_create_attribute_option(self):
        """Test creating an attribute option."""
        option = ProductAttributeOption.objects.create(
            attribute=self.attribute,
            value="red",
            display_name="Red",
            color_code="#FF0000"
        )
        
        assert option.attribute == self.attribute
        assert option.value == "red"
        assert option.display_name == "Red"
        assert option.color_code == "#FF0000"
        assert str(option) == "Color: Red"


@pytest.mark.django_db
class TestProductAttributeValueModel:
    """Test ProductAttributeValue model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Electronics",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            is_active=True
        )

    def test_create_text_attribute_value(self):
        """Test creating a text attribute value."""
        attribute = ProductAttribute.objects.create(
            name="Description", code="desc", type="text"
        )
        
        value = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=attribute,
            value_text="This is a test product"
        )
        
        assert value.product == self.product
        assert value.attribute == attribute
        assert value.value_text == "This is a test product"

    def test_create_integer_attribute_value(self):
        """Test creating an integer attribute value."""
        attribute = ProductAttribute.objects.create(
            name="Count", code="count", type="integer"
        )
        
        value = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=attribute,
            value_integer=42
        )
        
        assert value.product == self.product
        assert value.attribute == attribute
        assert value.value_integer == 42

    def test_create_decimal_attribute_value(self):
        """Test creating a decimal attribute value."""
        attribute = ProductAttribute.objects.create(
            name="Weight", code="weight", type="decimal"
        )
        
        value = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=attribute,
            value_decimal=Decimal("1.5")
        )
        
        assert value.product == self.product
        assert value.attribute == attribute
        assert value.value_decimal == Decimal("1.5")

    def test_create_boolean_attribute_value(self):
        """Test creating a boolean attribute value."""
        attribute = ProductAttribute.objects.create(
            name="Waterproof", code="waterproof", type="boolean"
        )
        
        value = ProductAttributeValue.objects.create(
            product=self.product,
            attribute=attribute,
            value_boolean=True
        )
        
        assert value.product == self.product
        assert value.attribute == attribute
        assert value.value_boolean is True


@pytest.mark.django_db
class TestProductImageModel:
    """Test ProductImage model functionality."""

    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Electronics",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            base_price=Decimal("99.99"),
            is_active=True
        )

    def test_create_product_image(self):
        """Test creating a product image."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
            alt_text="Test product image",
            sort_order=1
        )
        
        assert image.product == self.product
        assert image.image == "products/test.jpg"
        assert image.alt_text == "Test product image"
        assert image.sort_order == 1
        assert str(image) == f"Image for {self.product.name}"

    def test_product_image_primary(self):
        """Test primary image functionality."""
        image1 = ProductImage.objects.create(
            product=self.product,
            image="products/test1.jpg",
            is_primary=True
        )
        
        image2 = ProductImage.objects.create(
            product=self.product,
            image="products/test2.jpg",
            is_primary=True  # This should make image1 non-primary
        )
        
        image1.refresh_from_db()
        
        assert image1.is_primary is False
        assert image2.is_primary is True
