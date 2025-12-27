"""
Middleware for error handling and user-friendly error messages
"""

from django.shortcuts import render
from django.db.utils import OperationalError, DatabaseError, IntegrityError
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseServerError
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class DatabaseErrorHandlingMiddleware:
    """
    Middleware to catch database errors and show user-friendly messages

    This middleware intercepts database connection errors, timeouts,
    and other database issues to provide clear, actionable error messages
    instead of technical stack traces.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Process exceptions and return user-friendly error pages
        """

        # DATABASE CONNECTION ERRORS
        if isinstance(exception, OperationalError):
            error_msg = str(exception).lower()

            if 'connection refused' in error_msg or 'could not connect' in error_msg:
                logger.error(f"Database connection error: {exception}", exc_info=True)
                return render(request, 'errors/database_connection.html', {
                    'error_type': 'Database Connection Error',
                    'error_message': 'Unable to connect to the database',
                    'user_message': 'The database server is currently unavailable. Please try again in a few moments.',
                    'impact': 'You cannot view or update any data until the connection is restored.',
                    'actions': [
                        'Wait a few moments and refresh the page',
                        'Contact IT support if the issue persists',
                        'Check if other users are experiencing the same issue'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=503)

            elif 'timeout' in error_msg or 'timed out' in error_msg:
                logger.error(f"Database timeout error: {exception}", exc_info=True)
                return render(request, 'errors/database_timeout.html', {
                    'error_type': 'Database Timeout',
                    'error_message': 'The database query took too long to complete',
                    'user_message': 'The system is taking longer than expected to load this page. This might be due to high server load or a complex query.',
                    'impact': 'The page you requested could not be loaded in time.',
                    'actions': [
                        'Try refreshing the page',
                        'Simplify your search or filter criteria',
                        'Try again during off-peak hours',
                        'Contact support if this happens frequently'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=504)

            else:
                logger.error(f"Database operational error: {exception}", exc_info=True)
                return render(request, 'errors/database_error.html', {
                    'error_type': 'Database Error',
                    'error_message': 'A database error occurred',
                    'user_message': 'We encountered an unexpected database issue while processing your request.',
                    'impact': 'Your request could not be completed.',
                    'actions': [
                        'Try again in a few moments',
                        'Contact support if the problem continues',
                        'Save any work you were doing elsewhere if possible'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=500)

        # DATABASE INTEGRITY ERRORS
        elif isinstance(exception, IntegrityError):
            logger.error(f"Data integrity error: {exception}", exc_info=True)
            error_msg = str(exception).lower()

            if 'unique constraint' in error_msg or 'duplicate key' in error_msg:
                return render(request, 'errors/duplicate_data.html', {
                    'error_type': 'Duplicate Data',
                    'error_message': 'This record already exists',
                    'user_message': 'The data you are trying to save already exists in the system. Each record must be unique.',
                    'impact': 'Your changes were not saved.',
                    'actions': [
                        'Check if a similar record already exists',
                        'Modify your data to make it unique',
                        'Contact support if you believe this is an error'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=400)

            else:
                return render(request, 'errors/data_validation.html', {
                    'error_type': 'Data Validation Error',
                    'error_message': 'Invalid data was provided',
                    'user_message': 'The data you provided violates database constraints or rules.',
                    'impact': 'Your changes were not saved.',
                    'actions': [
                        'Review the data you entered',
                        'Ensure all required fields are filled correctly',
                        'Contact support if you need assistance'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=400)

        # CONCURRENCY / VERSION CONFLICT
        elif isinstance(exception, ValidationError):
            error_msg = str(exception).lower()
            if 'modified by another user' in error_msg or 'version' in error_msg:
                logger.warning(f"Concurrent modification detected: {exception}")
                return render(request, 'errors/concurrent_edit.html', {
                    'error_type': 'Concurrent Edit Conflict',
                    'error_message': 'Someone else modified this record',
                    'user_message': 'This record was changed by another user while you were editing it.',
                    'impact': 'Your changes were not saved to prevent data loss.',
                    'actions': [
                        'Refresh the page to see the latest data',
                        'Copy your changes to a safe place first',
                        'Review the current data and make your changes again',
                        'Coordinate with your team to avoid editing the same records simultaneously'
                    ],
                    'technical_details': str(exception) if request.user.is_staff else None
                }, status=409)

        # RADAR SYSTEM CONNECTION (placeholder for future implementation)
        # This would handle errors from external RADAR system
        # For now, we'll just log it
        logger.error(f"Unhandled exception: {exception}", exc_info=True)
        return None  # Let Django's default error handling take over


class ConcurrencyWarningMiddleware:
    """
    Middleware to add concurrency warnings to forms

    Adds the current version number to form templates
    so we can detect concurrent edits
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        """
        Add version info to context for forms
        """
        if hasattr(response, 'context_data') and response.context_data:
            # Add a flag to indicate concurrent editing is being monitored
            response.context_data['monitor_concurrency'] = True

        return response
