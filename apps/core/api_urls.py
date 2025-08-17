"""
API URL configuration for the ecommerce application.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.catalog.api import ProductViewSet
from apps.cart.api import CartItemViewSet
from apps.orders.api import CheckoutAPIView

# Create router for viewsets
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart/items', CartItemViewSet, basename='cartitem')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Checkout API
    path('checkout/', CheckoutAPIView.as_view(), name='api_checkout'),
]