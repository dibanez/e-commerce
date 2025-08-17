"""
Core views for the ecommerce application.
"""
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.catalog.models import Category, Product


class HomeView(TemplateView):
    """
    Home page view.
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get featured products
        featured_products = Product.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related('category').prefetch_related('images')[:8]
        
        # Get main categories
        main_categories = Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related('children')[:6]
        
        context.update({
            'featured_products': featured_products,
            'main_categories': main_categories,
        })
        
        return context


def handler404(request, exception):
    """
    Custom 404 error handler.
    """
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, 'errors/500.html', status=500)