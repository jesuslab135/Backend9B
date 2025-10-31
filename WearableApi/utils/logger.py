"""
Custom Logger Configuration
===========================
Singleton pattern implementation for application-wide logging.
Provides structured logging with different levels and file outputs.

Usage:
    from utils.logger import Logger
    
    logger = Logger.get_logger(__name__)
    logger.info("User logged in", extra={'user_id': 123})
    logger.error("Failed to save data", exc_info=True)
"""

import logging
import os
from pathlib import Path
from datetime import datetime


class Logger:
    """
    Singleton Logger class for centralized logging configuration.
    
    Design Pattern: Singleton
    Ensures only one logger instance exists throughout the application.
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logging()
        return cls._instance
    
    def _initialize_logging(self):
        """Initialize logging configuration"""
        # Create logs directory if it doesn't exist
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Define log format
        self.log_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Define detailed format for file logs
        self.detailed_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] '
            '[%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_file_handler(self, filename, level, formatter):
        """
        Create a file handler with rotation
        
        Args:
            filename: Name of log file
            level: Logging level
            formatter: Log formatter
        
        Returns:
            logging.FileHandler: Configured file handler
        """
        filepath = self.log_dir / filename
        handler = logging.FileHandler(filepath, encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
    
    def _create_console_handler(self, level):
        """
        Create a console handler for stdout
        
        Args:
            level: Logging level
        
        Returns:
            logging.StreamHandler: Configured console handler
        """
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(self.log_format)
        return handler
    
    @classmethod
    def get_logger(cls, name):
        """
        Get or create a logger instance
        
        Args:
            name: Logger name (usually __name__ of the module)
        
        Returns:
            logging.Logger: Configured logger instance
        
        Example:
            logger = Logger.get_logger(__name__)
            logger.info("Application started")
        """
        instance = cls()
        
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers = []
        
        # Console handler (INFO and above)
        console_handler = instance._create_console_handler(logging.INFO)
        logger.addHandler(console_handler)
        
        # DEBUG file handler (all messages)
        debug_handler = instance._create_file_handler(
            'debug.log',
            logging.DEBUG,
            instance.detailed_format
        )
        logger.addHandler(debug_handler)
        
        # INFO file handler
        info_handler = instance._create_file_handler(
            'info.log',
            logging.INFO,
            instance.log_format
        )
        logger.addHandler(info_handler)
        
        # ERROR file handler (ERROR and CRITICAL)
        error_handler = instance._create_file_handler(
            'error.log',
            logging.ERROR,
            instance.detailed_format
        )
        logger.addHandler(error_handler)
        
        # CRITICAL file handler (only CRITICAL)
        critical_handler = instance._create_file_handler(
            'critical.log',
            logging.CRITICAL,
            instance.detailed_format
        )
        logger.addHandler(critical_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    Design Pattern: Mixin
    Provides reusable logging functionality across multiple classes.
    
    Usage:
        class MyView(LoggerMixin, APIView):
            def get(self, request):
                self.logger.info("GET request received")
                return Response(data)
    """
    
    @property
    def logger(self):
        """
        Get logger instance for the class
        
        Returns:
            logging.Logger: Logger instance
        """
        if not hasattr(self, '_logger'):
            self._logger = Logger.get_logger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger


def log_exception(logger, exception, context=None):
    """
    Helper function to log exceptions with context
    
    Args:
        logger: Logger instance
        exception: Exception object
        context: Additional context dictionary
    
    Example:
        try:
            # some operation
        except Exception as e:
            log_exception(logger, e, {'user_id': 123})
    """
    error_msg = f"{type(exception).__name__}: {str(exception)}"
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_msg = f"{error_msg} | Context: {context_str}"
    
    logger.error(error_msg, exc_info=True)


def log_request(logger, request, response_status=None):
    """
    Helper function to log HTTP requests
    
    Args:
        logger: Logger instance
        request: Django request object
        response_status: HTTP response status code
    
    Example:
        log_request(logger, request, 200)
    """
    user = getattr(request, 'user', None)
    user_info = f"User: {user}" if user else "Anonymous"
    
    log_msg = f"{request.method} {request.path} | {user_info}"
    
    if response_status:
        log_msg += f" | Status: {response_status}"
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        log_msg += f" | Data: {request.data if hasattr(request, 'data') else 'N/A'}"
    
    logger.info(log_msg)


# Example usage and testing
if __name__ == "__main__":
    # Test logger
    logger = Logger.get_logger("test")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("\nLog files created in 'logs/' directory:")
    print("- debug.log (all messages)")
    print("- info.log (info, warning, error, critical)")
    print("- error.log (error, critical)")
    print("- critical.log (critical only)")