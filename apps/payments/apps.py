"""
App configuration for payments app.
"""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'
    
    def ready(self):
        # Load payment providers on app startup
        from .registry import registry
        registry.load_providers()