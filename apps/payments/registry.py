"""
Payment provider registry for dynamic loading and management.
"""
import importlib
import logging
from typing import Dict, List, Optional, Type

from django.conf import settings

from .base import PaymentProvider

logger = logging.getLogger(__name__)


class PaymentProviderRegistry:
    """
    Registry for payment providers with dynamic loading capabilities.
    """
    
    def __init__(self):
        self._providers: Dict[str, Type[PaymentProvider]] = {}
        self._instances: Dict[str, PaymentProvider] = {}
        self._loaded = False
    
    def load_providers(self) -> None:
        """
        Load payment providers from settings.
        """
        if self._loaded:
            return
        
        provider_classes = getattr(settings, 'PAYMENT_PROVIDERS', [])
        
        for provider_path in provider_classes:
            try:
                self._load_provider_class(provider_path)
            except Exception as e:
                logger.error(f"Failed to load payment provider {provider_path}: {e}")
        
        self._loaded = True
        logger.info(f"Loaded {len(self._providers)} payment providers")
    
    def _load_provider_class(self, provider_path: str) -> None:
        """
        Load a single provider class from import path.
        """
        try:
            # Split module path and class name
            module_path, class_name = provider_path.rsplit('.', 1)
            
            # Import module
            module = importlib.import_module(module_path)
            
            # Get provider class
            provider_class = getattr(module, class_name)
            
            # Validate that it's a PaymentProvider subclass
            if not issubclass(provider_class, PaymentProvider):
                raise ValueError(f"{provider_path} is not a PaymentProvider subclass")
            
            # Check if provider has required attributes
            if not provider_class.code:
                raise ValueError(f"{provider_path} must define a 'code' attribute")
            
            # Register provider
            self._providers[provider_class.code] = provider_class
            logger.debug(f"Registered payment provider: {provider_class.code}")
            
        except Exception as e:
            logger.error(f"Failed to load provider {provider_path}: {e}")
            raise
    
    def get_provider_class(self, code: str) -> Optional[Type[PaymentProvider]]:
        """
        Get provider class by code.
        """
        self.load_providers()
        return self._providers.get(code)
    
    def get_provider(self, code: str, config: Optional[Dict] = None) -> Optional[PaymentProvider]:
        """
        Get provider instance by code.
        """
        self.load_providers()
        
        # Check if we have a cached instance with the same config
        cache_key = f"{code}_{hash(str(sorted((config or {}).items())))}"
        
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        # Create new instance
        provider_class = self._providers.get(code)
        if not provider_class:
            return None
        
        try:
            instance = provider_class(config=config)
            self._instances[cache_key] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create provider instance {code}: {e}")
            return None
    
    def get_all_providers(self) -> Dict[str, Type[PaymentProvider]]:
        """
        Get all registered provider classes.
        """
        self.load_providers()
        return self._providers.copy()
    
    def get_available_providers(self, config_dict: Optional[Dict] = None) -> List[PaymentProvider]:
        """
        Get list of available provider instances.
        """
        self.load_providers()
        providers = []
        
        for code, provider_class in self._providers.items():
            try:
                # Get provider-specific config if available
                provider_config = None
                if config_dict and code in config_dict:
                    provider_config = config_dict[code]
                
                instance = self.get_provider(code, provider_config)
                if instance:
                    providers.append(instance)
            except Exception as e:
                logger.error(f"Failed to initialize provider {code}: {e}")
        
        return providers
    
    def is_provider_available(self, code: str) -> bool:
        """
        Check if a provider is available.
        """
        self.load_providers()
        return code in self._providers
    
    def register_provider(self, provider_class: Type[PaymentProvider]) -> None:
        """
        Manually register a provider class.
        """
        if not issubclass(provider_class, PaymentProvider):
            raise ValueError("Provider must be a PaymentProvider subclass")
        
        if not provider_class.code:
            raise ValueError("Provider must define a 'code' attribute")
        
        self._providers[provider_class.code] = provider_class
        logger.debug(f"Manually registered payment provider: {provider_class.code}")
    
    def unregister_provider(self, code: str) -> None:
        """
        Unregister a provider.
        """
        if code in self._providers:
            del self._providers[code]
        
        # Remove cached instances
        keys_to_remove = [k for k in self._instances.keys() if k.startswith(f"{code}_")]
        for key in keys_to_remove:
            del self._instances[key]
        
        logger.debug(f"Unregistered payment provider: {code}")
    
    def clear_cache(self) -> None:
        """
        Clear cached provider instances.
        """
        self._instances.clear()
        logger.debug("Cleared payment provider instance cache")
    
    def reload(self) -> None:
        """
        Reload all providers from settings.
        """
        self._providers.clear()
        self._instances.clear()
        self._loaded = False
        self.load_providers()
        logger.info("Reloaded payment providers")


# Global registry instance
registry = PaymentProviderRegistry()


# Convenience functions
def get_provider(code: str, config: Optional[Dict] = None) -> Optional[PaymentProvider]:
    """
    Get payment provider instance by code.
    """
    return registry.get_provider(code, config)


def get_available_providers(config_dict: Optional[Dict] = None) -> List[PaymentProvider]:
    """
    Get list of available payment providers.
    """
    return registry.get_available_providers(config_dict)


def is_provider_available(code: str) -> bool:
    """
    Check if payment provider is available.
    """
    return registry.is_provider_available(code)