"""
Development settings for ecommerce project.
"""
from .base import *  # noqa

# Debug settings
DEBUG = True

# Add debug toolbar - temporarily disabled
# THIRD_PARTY_APPS += ['debug_toolbar']  # noqa
# MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Disable security features in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Django Debug Toolbar configuration
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'SHOW_COLLAPSED': True,
}

# Static files configuration for development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Django extensions (if needed)
try:
    import django_extensions  # noqa
    THIRD_PARTY_APPS += ['django_extensions']  # noqa
except ImportError:
    pass

# Override logging for development - disable file logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Payment settings for development
DUMMY_PAYMENT_SUCCESS_RATE = env('DUMMY_PAYMENT_SUCCESS_RATE', default=100)