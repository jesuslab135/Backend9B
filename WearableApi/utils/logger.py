
import logging
import os
from pathlib import Path
from datetime import datetime

class Logger:
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logging()
        return cls._instance
    
    def _initialize_logging(self):
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.detailed_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] '
            '[%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_file_handler(self, filename, level, formatter):
        filepath = self.log_dir / filename
        handler = logging.FileHandler(filepath, encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
    
    def _create_console_handler(self, level):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(self.log_format)
        return handler
    
    @classmethod
    def get_logger(cls, name):
        instance = cls()
        
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        logger.handlers = []
        
        console_handler = instance._create_console_handler(logging.INFO)
        logger.addHandler(console_handler)
        
        debug_handler = instance._create_file_handler(
            'debug.log',
            logging.DEBUG,
            instance.detailed_format
        )
        logger.addHandler(debug_handler)
        
        info_handler = instance._create_file_handler(
            'info.log',
            logging.INFO,
            instance.log_format
        )
        logger.addHandler(info_handler)
        
        error_handler = instance._create_file_handler(
            'error.log',
            logging.ERROR,
            instance.detailed_format
        )
        logger.addHandler(error_handler)
        
        critical_handler = instance._create_file_handler(
            'critical.log',
            logging.CRITICAL,
            instance.detailed_format
        )
        logger.addHandler(critical_handler)
        
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger

class LoggerMixin:
    
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = Logger.get_logger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger

def log_exception(logger, exception, context=None):
    error_msg = f"{type(exception).__name__}: {str(exception)}"
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_msg = f"{error_msg} | Context: {context_str}"
    
    logger.error(error_msg, exc_info=True)

def log_request(logger, request, response_status=None):
    user = getattr(request, 'user', None)
    user_info = f"User: {user}" if user else "Anonymous"
    
    log_msg = f"{request.method} {request.path} | {user_info}"
    
    if response_status:
        log_msg += f" | Status: {response_status}"
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        log_msg += f" | Data: {request.data if hasattr(request, 'data') else 'N/A'}"
    
    logger.info(log_msg)

if __name__ == "__main__":
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

