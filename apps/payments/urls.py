"""
URL configuration for payments app.
"""
from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Payment method selection
    path('methods/<str:order_number>/', views.PaymentMethodSelectionView.as_view(), name='payment_methods'),
    
    # Payment initiation
    path('initiate/<str:order_number>/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    
    # Payment return (after payment at provider)
    path('return/<str:order_number>/<str:provider_code>/', views.PaymentReturnView.as_view(), name='payment_return'),
    
    # Webhook endpoints
    path('webhook/<str:provider_code>/', views.PaymentWebhookView.as_view(), name='payment_webhook'),
    
    # Payment status check
    path('status/<uuid:payment_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    
    # Success/failure pages
    path('success/<str:order_number>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('failure/<str:order_number>/', views.PaymentFailureView.as_view(), name='payment_failure'),
]