"""
Production settings for ecommerce project.
"""
from .base import *  # noqa

# Debug settings
DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = env('SECURE_HSTS_SECONDS', default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = env('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env('SECURE_HSTS_PRELOAD', default=True)

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', default=[])

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Static files configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cache configuration (Redis recommended for production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session configuration for production
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# Database connection pooling (optional, if using django-db-pool)
# DATABASES['default']['OPTIONS'] = {
#     'MAX_CONNS': 20,
#     'MIN_CONNS': 5,
# }

# Sentry configuration (if using Sentry for error tracking)
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.logging import LoggingIntegration

# sentry_logging = LoggingIntegration(
#     level=logging.INFO,
#     event_level=logging.ERROR
# )

# sentry_sdk.init(
#     dsn=env('SENTRY_DSN', default=''),
#     integrations=[DjangoIntegration(), sentry_logging],
#     traces_sample_rate=0.1,
#     send_default_pii=True
# )

# Override logging for production
LOGGING['handlers']['file']['filename'] = '/app/logs/django.log'  # noqa
LOGGING['root']['level'] = 'INFO'  # noqa
LOGGING['loggers']['django']['level'] = 'INFO'  # noqa
LOGGING['loggers']['apps']['level'] = 'INFO'  # noqa