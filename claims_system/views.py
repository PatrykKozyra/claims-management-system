"""
Views for claims_system project.
"""

from django.shortcuts import render


def ratelimit_error(request, exception=None):
    """
    View to handle rate limit errors.
    """
    return render(request, '429.html', status=429)


def handler404(request, exception=None):
    """
    Custom 404 error handler.
    """
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, '500.html', status=500)


def handler403(request, exception=None):
    """
    Custom 403 error handler.
    """
    return render(request, '403.html', status=403)
