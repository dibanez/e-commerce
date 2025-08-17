"""
Catalog models for the ecommerce application.
"""
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Product category model with hierarchical structure.
    """
    name = models.CharField('name', max_length=100, unique=True)
    slug = models.SlugField('slug', max_length=100, unique=True, blank=True)
    description = models.TextField('description', blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='parent category'
    )
    image = models.ImageField(
        'image',
        upload_to='categories/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField('active', default=True)
    sort_order = models.PositiveIntegerField('sort order', default=0)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        db_table = 'catalog_category'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})

    @property
    def full_path(self) -> str:
        """
        Get the full category path (e.g., 'Electronics > Computers > Laptops').
        """
        path = [self.name]
        parent = self.parent
        while parent:
            path.append(parent.name)
            parent = parent.parent
        return ' > '.join(reversed(path))

    def get_descendants(self, include_self=False):
        """
        Get all descendant categories.
        """
        descendants = []
        if include_self:
            descendants.append(self)
        
        for child in self.children.all():
            descendants.extend(child.get_descendants(include_self=True))
        
        return descendants


class Product(models.Model):
    """
    Product model with basic information.
    """
    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]

    name = models.CharField('name', max_length=200)
    slug = models.SlugField('slug', max_length=200, unique=True, blank=True)
    description = models.TextField('description', blank=True)
    short_description = models.CharField('short description', max_length=500, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='category'
    )
    sku = models.CharField(
        'SKU',
        max_length=50,
        unique=True,
        help_text='Stock Keeping Unit'
    )
    base_price = models.DecimalField(
        'base price',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        'currency',
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR'
    )
    cost_price = models.DecimalField(
        'cost price',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    weight = models.DecimalField(
        'weight (kg)',
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    dimensions = models.CharField(
        'dimensions (L x W x H)',
        max_length=100,
        blank=True,
        help_text='Format: length x width x height in cm'
    )
    stock_quantity = models.PositiveIntegerField('stock quantity', default=0)
    track_inventory = models.BooleanField('track inventory', default=True)
    allow_backorders = models.BooleanField('allow backorders', default=False)
    is_active = models.BooleanField('active', default=True)
    is_featured = models.BooleanField('featured', default=False)
    meta_title = models.CharField('meta title', max_length=200, blank=True)
    meta_description = models.CharField('meta description', max_length=300, blank=True)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'product'
        verbose_name_plural = 'products'
        db_table = 'catalog_product'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self) -> bool:
        """
        Check if product is in stock.
        """
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorders

    @property
    def formatted_price(self) -> str:
        """
        Get formatted price with currency symbol.
        """
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{self.base_price} {symbol}"

    def get_attribute_values(self):
        """
        Get all attribute values for this product.
        """
        return self.attribute_values.select_related('attribute', 'value_option').all()


class ProductImage(models.Model):
    """
    Product image model for multiple images per product.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='product'
    )
    image = models.ImageField('image', upload_to='products/')
    alt_text = models.CharField('alt text', max_length=200, blank=True)
    sort_order = models.PositiveIntegerField('sort order', default=0)
    is_primary = models.BooleanField('primary image', default=False)
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'product image'
        verbose_name_plural = 'product images'
        db_table = 'catalog_productimage'
        ordering = ['sort_order', 'created_at']

    def __str__(self) -> str:
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs) -> None:
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """
    Product attribute definition (e.g., Color, Size, Material).
    """
    ATTRIBUTE_TYPES = [
        ('text', 'Text'),
        ('integer', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('enum', 'Enumeration'),
    ]

    name = models.CharField('name', max_length=100)
    code = models.CharField(
        'code',
        max_length=50,
        unique=True,
        help_text='Unique code for this attribute (e.g., color, size)'
    )
    type = models.CharField(
        'type',
        max_length=20,
        choices=ATTRIBUTE_TYPES,
        default='text'
    )
    description = models.TextField('description', blank=True)
    is_required = models.BooleanField('required', default=False)
    is_filterable = models.BooleanField('filterable', default=True)
    sort_order = models.PositiveIntegerField('sort order', default=0)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'product attribute'
        verbose_name_plural = 'product attributes'
        db_table = 'catalog_productattribute'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class ProductAttributeOption(models.Model):
    """
    Options for enumeration-type attributes (e.g., Red, Blue, Green for Color).
    """
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='options',
        limit_choices_to={'type': 'enum'},
        verbose_name='attribute'
    )
    value = models.CharField('value', max_length=100)
    display_name = models.CharField('display name', max_length=100, blank=True)
    color_code = models.CharField(
        'color code',
        max_length=7,
        blank=True,
        help_text='Hex color code for visual representation (e.g., #FF0000)'
    )
    sort_order = models.PositiveIntegerField('sort order', default=0)
    is_active = models.BooleanField('active', default=True)

    class Meta:
        verbose_name = 'product attribute option'
        verbose_name_plural = 'product attribute options'
        db_table = 'catalog_productattributeoption'
        ordering = ['sort_order', 'value']
        unique_together = [['attribute', 'value']]

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.display_name or self.value}"


class ProductAttributeValue(models.Model):
    """
    Attribute values for products (EAV pattern).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name='product'
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name='attribute'
    )
    
    # Value fields for different types
    value_text = models.TextField('text value', blank=True, null=True)
    value_integer = models.IntegerField('integer value', blank=True, null=True)
    value_decimal = models.DecimalField(
        'decimal value',
        max_digits=15,
        decimal_places=4,
        blank=True,
        null=True
    )
    value_boolean = models.BooleanField('boolean value', blank=True, null=True)
    value_date = models.DateField('date value', blank=True, null=True)
    value_option = models.ForeignKey(
        ProductAttributeOption,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='option value'
    )
    
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    class Meta:
        verbose_name = 'product attribute value'
        verbose_name_plural = 'product attribute values'
        db_table = 'catalog_productattributevalue'
        unique_together = [['product', 'attribute']]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.attribute.name}: {self.get_value()}"

    def get_value(self):
        """
        Get the actual value based on the attribute type.
        """
        type_mapping = {
            'text': self.value_text,
            'integer': self.value_integer,
            'decimal': self.value_decimal,
            'boolean': self.value_boolean,
            'date': self.value_date,
            'enum': self.value_option.display_name if self.value_option else None,
        }
        return type_mapping.get(self.attribute.type)

    def set_value(self, value):
        """
        Set the value based on the attribute type.
        """
        # Clear all value fields first
        self.value_text = None
        self.value_integer = None
        self.value_decimal = None
        self.value_boolean = None
        self.value_date = None
        self.value_option = None

        # Set the appropriate field based on attribute type
        if self.attribute.type == 'text':
            self.value_text = str(value) if value is not None else None
        elif self.attribute.type == 'integer':
            self.value_integer = int(value) if value is not None else None
        elif self.attribute.type == 'decimal':
            self.value_decimal = Decimal(str(value)) if value is not None else None
        elif self.attribute.type == 'boolean':
            self.value_boolean = bool(value) if value is not None else None
        elif self.attribute.type == 'date':
            self.value_date = value
        elif self.attribute.type == 'enum' and isinstance(value, ProductAttributeOption):
            self.value_option = value

    def clean(self):
        """
        Validate that only the appropriate value field is set.
        """
        from django.core.exceptions import ValidationError
        
        # Count non-null value fields
        value_fields = [
            self.value_text, self.value_integer, self.value_decimal,
            self.value_boolean, self.value_date, self.value_option
        ]
        non_null_count = sum(1 for field in value_fields if field is not None)
        
        if non_null_count != 1:
            raise ValidationError(_("Exactly one value field must be set."))
        
        # Validate that the correct field is set for the attribute type
        expected_field_map = {
            'text': self.value_text,
            'integer': self.value_integer,
            'decimal': self.value_decimal,
            'boolean': self.value_boolean,
            'date': self.value_date,
            'enum': self.value_option,
        }
        
        expected_field = expected_field_map.get(self.attribute.type)
        if expected_field is None:
            raise ValidationError(
                _(f"Value field for type '{self.attribute.type}' is not set.")
            )