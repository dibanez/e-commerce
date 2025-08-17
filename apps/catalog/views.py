"""
Views for catalog app.
"""
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Category, Product, ProductAttributeValue


class ProductListView(ListView):
    """
    View for listing products with filtering capabilities.
    """
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Filter by category if specified
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                # Include products from subcategories
                categories = category.get_descendants(include_self=True)
                queryset = queryset.filter(category__in=categories)
                self.category = category
            except Category.DoesNotExist:
                pass
        
        # Filter by attribute values
        for key, value in self.request.GET.items():
            if key.startswith('attr_'):
                attribute_code = key[5:]  # Remove 'attr_' prefix
                queryset = queryset.filter(
                    attribute_values__attribute__code=attribute_code,
                    attribute_values__value_text=value
                )
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            parent=None, is_active=True
        ).prefetch_related('children')
        context['current_category'] = getattr(self, 'category', None)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class CategoryDetailView(DetailView):
    """
    View for category detail page.
    """
    model = Category
    template_name = 'catalog/category_detail.html'
    context_object_name = 'category'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products in this category and subcategories
        categories = self.object.get_descendants(include_self=True)
        products = Product.objects.filter(
            category__in=categories,
            is_active=True
        ).select_related('category').prefetch_related('images')
        
        context['products'] = products[:12]  # Limit for performance
        context['subcategories'] = self.object.children.filter(is_active=True)
        
        return context


class ProductDetailView(DetailView):
    """
    View for product detail page.
    """
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get product images
        context['images'] = self.object.images.all()
        
        # Get product attributes
        attribute_values = ProductAttributeValue.objects.filter(
            product=self.object
        ).select_related('attribute', 'value_option').order_by('attribute__sort_order')
        
        context['attribute_values'] = attribute_values
        
        # Get related products from the same category
        related_products = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(pk=self.object.pk)[:4]
        
        context['related_products'] = related_products
        
        return context


class ProductSearchView(ListView):
    """
    View for product search functionality.
    """
    model = Product
    template_name = 'catalog/product_search.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        
        if not query:
            return Product.objects.none()
        
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(sku__icontains=query),
            is_active=True
        ).select_related('category').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['total_results'] = self.get_queryset().count()
        return context