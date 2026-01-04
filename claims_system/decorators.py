"""
Custom decorators for the claims management system.
"""

from functools import wraps
from django.conf import settings
from django.http import HttpResponse
from django_ratelimit.decorators import ratelimit


def login_rate_limit(func):
    """
    Rate limit decorator for login views.
    Limits to 5 attempts per 5 minutes by default.
    """
    rate = settings.config('LOGIN_RATE_LIMIT', default='5/5m') if hasattr(settings, 'config') else '5/5m'

    @ratelimit(key='ip', rate=rate, method='POST', block=True)
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)

    return wrapper


def export_rate_limit(func):
    """
    Rate limit decorator for export views.
    Limits to 10 requests per hour by default.
    """
    rate = settings.config('EXPORT_RATE_LIMIT', default='10/h') if hasattr(settings, 'config') else '10/h'

    @ratelimit(key='user', rate=rate, method='GET', block=True)
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)

    return wrapper


def api_rate_limit(rate='100/h'):
    """
    Configurable rate limit decorator for API endpoints.

    Usage:
        @api_rate_limit('50/h')
        def my_api_view(request):
            ...
    """
    def decorator(func):
        @ratelimit(key='user_or_ip', rate=rate, method=['GET', 'POST'], block=True)
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
