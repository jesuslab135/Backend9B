
from functools import wraps
from utils.logger import Logger, log_exception, log_request

def log_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = Logger.get_logger(func.__module__)
        
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
            import time
            start_time = time.time()
            
            response = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
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
            raise
    
    return wrapper

def log_database_operation(operation_type="database"):
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
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger.get_logger(func.__module__)
            
            import time
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
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

