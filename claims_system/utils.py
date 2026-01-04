"""
Utility functions for the claims management system.
"""

import logging
import time
from typing import Callable, Any, Optional
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_attempts: Optional[int] = None,
    delay: Optional[int] = None,
    exponential_backoff: bool = False,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts (default from settings)
        delay: Delay between retries in seconds (default from settings)
        exponential_backoff: Use exponential backoff for delays
        exceptions: Tuple of exceptions to catch and retry

    Usage:
        @retry_on_failure(max_attempts=3, delay=5)
        def sync_with_radar(voyage_id):
            ...
    """
    if max_attempts is None:
        max_attempts = getattr(settings, 'RADAR_SYNC_RETRY_ATTEMPTS', 3)
    if delay is None:
        delay = getattr(settings, 'RADAR_SYNC_RETRY_DELAY', 5)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts",
                            exc_info=True,
                            extra={
                                'function': func.__name__,
                                'attempts': attempt,
                                'args': args,
                                'kwargs': kwargs,
                            }
                        )
                        raise

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {current_delay} seconds...",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt,
                            'max_attempts': max_attempts,
                            'delay': current_delay,
                            'error': str(e),
                        }
                    )

                    time.sleep(current_delay)

                    if exponential_backoff:
                        current_delay *= 2

            return None

        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log the execution time of a function.

    Usage:
        @log_execution_time
        def expensive_operation():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        logger.info(
            f"Function {func.__name__} executed in {execution_time:.2f} seconds",
            extra={
                'function': func.__name__,
                'execution_time': execution_time,
            }
        )

        return result

    return wrapper


def safe_get_client_ip(request) -> str:
    """
    Safely get the client's IP address from the request.

    Args:
        request: Django request object

    Returns:
        Client IP address as string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import os
    import re

    # Get just the filename without path
    filename = os.path.basename(filename)

    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Limit filename length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename


def validate_file_security(uploaded_file) -> tuple[bool, Optional[str]]:
    """
    Perform additional security validation on uploaded files.

    Args:
        uploaded_file: Django UploadedFile object

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for null bytes in filename
    if '\0' in uploaded_file.name:
        return False, "Invalid filename contains null bytes"

    # Check for path traversal attempts
    if '..' in uploaded_file.name or '/' in uploaded_file.name or '\\' in uploaded_file.name:
        return False, "Invalid filename contains path traversal characters"

    # Check file extension matches content
    import mimetypes
    expected_mime = mimetypes.guess_type(uploaded_file.name)[0]
    if expected_mime and expected_mime != uploaded_file.content_type:
        logger.warning(
            f"MIME type mismatch: filename suggests {expected_mime} but file is {uploaded_file.content_type}",
            extra={
                'filename': uploaded_file.name,
                'expected_mime': expected_mime,
                'actual_mime': uploaded_file.content_type,
            }
        )
        # Don't reject, just log (some browsers send incorrect MIME types)

    return True, None
