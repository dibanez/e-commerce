"""
Django admin configuration for catalog app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Category, Product, ProductAttribute, ProductAttributeOption,
    ProductAttributeValue, ProductImage
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category model.
    """
    list_display = ('name', 'parent', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'sort_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display', {
            'fields': ('image', 'is_active', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ProductImageInline(admin.TabularInline):
    """
    Inline admin for ProductImage model.
    """
    model = ProductImage
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('image', 'alt_text', 'sort_order', 'is_primary', 'created_at')


class ProductAttributeValueInline(admin.TabularInline):
    """
    Inline admin for ProductAttributeValue model.
    """
    model = ProductAttributeValue
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Customize the form based on attribute type
        class CustomForm(formset.form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                # Hide irrelevant value fields based on attribute type
                if self.instance and self.instance.pk and hasattr(self.instance, 'attribute_id') and self.instance.attribute_id:
                    try:
                        attr_type = self.instance.attribute.type
                        field_mapping = {
                            'text': ['value_integer', 'value_decimal', 'value_boolean', 'value_date', 'value_option'],
                            'integer': ['value_text', 'value_decimal', 'value_boolean', 'value_date', 'value_option'],
                            'decimal': ['value_text', 'value_integer', 'value_boolean', 'value_date', 'value_option'],
                            'boolean': ['value_text', 'value_integer', 'value_decimal', 'value_date', 'value_option'],
                            'date': ['value_text', 'value_integer', 'value_decimal', 'value_boolean', 'value_option'],
                            'enum': ['value_text', 'value_integer', 'value_decimal', 'value_boolean', 'value_date'],
                        }
                        
                        fields_to_hide = field_mapping.get(attr_type, [])
                        for field_name in fields_to_hide:
                            if field_name in self.fields:
                                self.fields[field_name].widget.attrs['style'] = 'display: none;'
                    except (AttributeError, ProductAttribute.DoesNotExist):
                        # If attribute doesn't exist yet, don't hide any fields
                        pass
        
        formset.form = CustomForm
        return formset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model.
    """
    list_display = (
        'name', 'category', 'sku', 'formatted_price', 'stock_quantity',
        'is_active', 'is_featured', 'created_at'
    )
    list_filter = (
        'is_active', 'is_featured', 'category', 'currency', 'created_at'
    )
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'sku', 'category')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_inventory', 'allow_backorders')
        }),
        ('Physical Properties', {
            'fields': ('weight', 'dimensions'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, ProductAttributeValueInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductImage model.
    """
    list_display = ('product', 'alt_text', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('is_primary', 'sort_order')
    readonly_fields = ('created_at',)


class ProductAttributeOptionInline(admin.TabularInline):
    """
    Inline admin for ProductAttributeOption model.
    """
    model = ProductAttributeOption
    extra = 1
    fields = ('value', 'display_name', 'color_code', 'sort_order', 'is_active')
    
    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.type != 'enum':
            return 0
        return self.extra


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductAttribute model.
    """
    list_display = ('name', 'code', 'type', 'is_required', 'is_filterable', 'sort_order')
    list_filter = ('type', 'is_required', 'is_filterable', 'created_at')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_required', 'is_filterable', 'sort_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'type', 'description')
        }),
        ('Settings', {
            'fields': ('is_required', 'is_filterable', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductAttributeOptionInline]


@admin.register(ProductAttributeOption)
class ProductAttributeOptionAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductAttributeOption model.
    """
    list_display = ('attribute', 'value', 'display_name', 'color_preview', 'sort_order', 'is_active')
    list_filter = ('attribute', 'is_active')
    search_fields = ('attribute__name', 'value', 'display_name')
    list_editable = ('sort_order', 'is_active')
    
    def color_preview(self, obj):
        """
        Display a color preview if color_code is set.
        """
        if obj.color_code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div>',
                obj.color_code
            )
        return '-'
    color_preview.short_description = 'Color'


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductAttributeValue model.
    """
    list_display = ('product', 'attribute', 'get_value_display', 'created_at')
    list_filter = ('attribute', 'created_at')
    search_fields = ('product__name', 'attribute__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_value_display(self, obj):
        """
        Display the appropriate value based on attribute type.
        """
        return obj.get_value() or '-'
    get_value_display.short_description = 'Value'
    
    fieldsets = (
        (None, {
            'fields': ('product', 'attribute')
        }),
        ('Values', {
            'fields': (
                'value_text', 'value_integer', 'value_decimal',
                'value_boolean', 'value_date', 'value_option'
            ),
            'description': 'Only set the value field that matches the attribute type.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )