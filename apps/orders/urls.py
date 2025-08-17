"""
URL configuration for orders app.
"""
from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<str:number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<str:number>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),
]