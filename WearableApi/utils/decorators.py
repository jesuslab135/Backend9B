"""
Decorators for Logging and Error Handling
==========================================
Provides reusable decorators for endpoint logging and error handling.

Design Pattern: Decorator Pattern
Adds logging functionality without modifying original functions.
"""

from functools import wraps
from utils.logger import Logger, log_exception, log_request


def log_endpoint(func):
    """
    Decorator to automatically log API endpoint access
    
    Logs:
        - Method and path
        - Request data
        - Response status
        - Execution time
        - Any errors
    
    Usage:
        @log_endpoint
        def my_view(request):
            return Response(data)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = Logger.get_logger(func.__module__)
        
        # Get request object (first arg for functions, or from kwargs)
        request = None
        if args:
            request = args[0] if hasattr(args[0], 'method') else (
                args[1] if len(args) > 1 and hasattr(args[1], 'method') else None
            )
        
        if request:
            logger.info(
                f"⚡ Endpoint accessed: {request.method} {request.path} "
                f"| User: {getattr(request, 'user', 'Anonymous')}"
            )
        
        try:
            # Execute the actual function
            import time
            start_time = time.time()
            
            response = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            if request:
                status = getattr(response, 'status_code', 'N/A')
                logger.info(
                    f"✓ Response: {status} | Time: {execution_time:.2f}ms"
                )
            
            return response
            
        except Exception as e:
            if request:
                logger.error(
                    f"✗ Failed: {request.method} {request.path} | "
                    f"Error: {type(e).__name__}: {str(e)}"
                )
            log_exception(logger, e, {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            raise
    
    return wrapper


def log_errors(func):
    """
    Decorator to catch and log errors without stopping execution
    
    Usage:
        @log_errors
        def risky_operation():
            # code that might fail
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = Logger.get_logger(func.__module__)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_exception(logger, e, {
                'function': func.__name__,
                'module': func.__module__
            })
            # Re-raise the exception
            raise
    
    return wrapper


def log_database_operation(operation_type="database"):
    """
    Decorator factory for logging database operations
    
    Args:
        operation_type: Type of operation (create, update, delete, etc.)
    
    Usage:
        @log_database_operation("create")
        def create_user(data):
            return User.objects.create(**data)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger.get_logger(func.__module__)
            
            logger.debug(
                f"💾 Database {operation_type}: {func.__name__} started"
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"✓ Database {operation_type}: {func.__name__} completed"
                )
                return result
            except Exception as e:
                logger.error(
                    f"✗ Database {operation_type}: {func.__name__} failed - "
                    f"{type(e).__name__}: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def log_performance(threshold_ms=1000):
    """
    Decorator to log slow operations
    
    Args:
        threshold_ms: Threshold in milliseconds to log warning
    
    Usage:
        @log_performance(threshold_ms=500)
        def slow_operation():
            # potentially slow code
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger.get_logger(func.__module__)
            
            import time
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            if execution_time > threshold_ms:
                logger.warning(
                    f"⚠️  Slow operation: {func.__name__} took "
                    f"{execution_time:.2f}ms (threshold: {threshold_ms}ms)"
                )
            else:
                logger.debug(
                    f"⚡ {func.__name__} completed in {execution_time:.2f}ms"
                )
            
            return result
        
        return wrapper
    return decorator