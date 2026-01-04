"""
Custom middleware for the claims management system.
"""

import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to handle exceptions and provide user-friendly error messages.
    """

    def process_exception(self, request, exception):
        """
        Process exceptions and return appropriate error responses.
        """
        # Log the exception
        logger.error(
            f"Exception occurred: {exception}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                'ip_address': self.get_client_ip(request),
            }
        )

        # In production, return user-friendly error pages
        if not settings.DEBUG:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON for AJAX requests
                return JsonResponse({
                    'error': 'An unexpected error occurred. Please try again or contact support.',
                    'status': 'error'
                }, status=500)
            else:
                # Return HTML error page
                return render(request, '500.html', status=500)

        # In debug mode, let Django's default error handling take over
        return None

    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add additional security headers to responses.
    """

    def process_response(self, request, response):
        """
        Add security headers to the response.
        """
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
        )

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response


class FileUploadValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate file uploads for size and type.
    """

    def process_request(self, request):
        """
        Validate file uploads in the request.
        """
        if request.method in ['POST', 'PUT'] and request.FILES:
            max_size = settings.MAX_UPLOAD_SIZE
            allowed_extensions = settings.ALLOWED_UPLOAD_EXTENSIONS
            allowed_mime_types = settings.ALLOWED_UPLOAD_MIME_TYPES

            for file_field, uploaded_file in request.FILES.items():
                # Check file size
                if uploaded_file.size > max_size:
                    logger.warning(
                        f"File upload rejected: size {uploaded_file.size} exceeds limit {max_size}",
                        extra={
                            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'filename': uploaded_file.name,
                            'size': uploaded_file.size,
                        }
                    )
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'error': f'File size exceeds maximum allowed size of {max_size / 1024 / 1024}MB',
                            'status': 'error'
                        }, status=400)
                    else:
                        from django.contrib import messages
                        messages.error(
                            request,
                            f'File "{uploaded_file.name}" exceeds maximum allowed size of {max_size / 1024 / 1024}MB'
                        )
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(request.path)

                # Check file extension
                file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
                if file_extension not in allowed_extensions:
                    logger.warning(
                        f"File upload rejected: extension {file_extension} not allowed",
                        extra={
                            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'filename': uploaded_file.name,
                            'extension': file_extension,
                        }
                    )
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'error': f'File type "{file_extension}" is not allowed. Allowed types: {", ".join(allowed_extensions)}',
                            'status': 'error'
                        }, status=400)
                    else:
                        from django.contrib import messages
                        messages.error(
                            request,
                            f'File type "{file_extension}" is not allowed. Allowed types: {", ".join(allowed_extensions)}'
                        )
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(request.path)

                # Check MIME type
                content_type = uploaded_file.content_type
                if content_type not in allowed_mime_types:
                    logger.warning(
                        f"File upload rejected: MIME type {content_type} not allowed",
                        extra={
                            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'filename': uploaded_file.name,
                            'mime_type': content_type,
                        }
                    )
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'error': f'File MIME type "{content_type}" is not allowed',
                            'status': 'error'
                        }, status=400)
                    else:
                        from django.contrib import messages
                        messages.error(
                            request,
                            f'File type is not allowed for security reasons'
                        )
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(request.path)

        return None
