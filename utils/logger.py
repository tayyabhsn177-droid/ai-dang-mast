import logging
import logging.config
import json
import uuid
import time
import functools
from typing import Dict, Any, Optional
from datetime import datetime
from contextvars import ContextVar
from pathlib import Path
import os

# Context variable for correlation ID tracking
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(""),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry.update(extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """Filter to add correlation ID to all log records"""
    
    def filter(self, record):
        record.correlation_id = correlation_id.get("")
        return True

def setup_logging(config_path: Optional[str] = None, 
                 log_level: str = "INFO",
                 environment: str = "development"):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    if config_path and Path(config_path).exists():
        # Load from config file
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        # Default configuration
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "utils.logger.JSONFormatter"
                },
                "console": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "filters": {
                "correlation": {
                    "()": "utils.logger.ContextFilter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "console" if environment == "development" else "json",
                    "filters": ["correlation"],
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "json",
                    "filters": ["correlation"],
                    "filename": "logs/dungeon_master.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "json",
                    "filters": ["correlation"],
                    "filename": "logs/dungeon_master_errors.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "dungeon_master": {
                    "level": "DEBUG",
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["console"]
            }
        }
        
        logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the dungeon_master prefix"""
    return logging.getLogger(f"dungeon_master.{name}")

def set_correlation_id(corr_id: str = None) -> str:
    """Set correlation ID for request tracking"""
    if corr_id is None:
        corr_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    correlation_id.set(corr_id)
    return corr_id

def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id.get("")

class LoggingContext:
    """Context manager for logging with correlation ID"""
    
    def __init__(self, corr_id: str = None, **context):
        self.corr_id = corr_id or str(uuid.uuid4())[:8]
        self.context = context
        self.previous_corr_id = None
        
    def __enter__(self):
        self.previous_corr_id = correlation_id.get("")
        correlation_id.set(self.corr_id)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        correlation_id.set(self.previous_corr_id)

def log_performance(logger: logging.Logger = None):
    """Decorator to log function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger("performance")
            
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"
            
            logger.debug(
                f"Starting execution of {function_name}",
                extra={
                    "function": function_name,
                    "event": "function_start",
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                logger.info(
                    f"Completed execution of {function_name}",
                    extra={
                        "function": function_name,
                        "event": "function_complete",
                        "execution_time_ms": round(execution_time, 2),
                        "success": True
                    }
                )
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Error in {function_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        "function": function_name,
                        "event": "function_error",
                        "execution_time_ms": round(execution_time, 2),
                        "error_type": type(e).__name__,
                        "success": False
                    }
                )
                raise
                
        return wrapper
    return decorator

def log_game_event(event_type: str, **context):
    """Log game-specific events"""
    logger = get_logger("game_events")
    logger.info(
        f"Game event: {event_type}",
        extra={
            "event_type": event_type,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

def log_api_call(endpoint: str, method: str, status_code: int = None, 
                response_time_ms: float = None, **context):
    """Log API call details"""
    logger = get_logger("api")
    
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "event": "api_call"
    }
    
    if status_code:
        log_data["status_code"] = status_code
    if response_time_ms:
        log_data["response_time_ms"] = round(response_time_ms, 2)
    
    log_data.update(context)
    
    if status_code and status_code >= 400:
        logger.warning(f"API call failed: {method} {endpoint}", extra=log_data)
    else:
        logger.info(f"API call: {method} {endpoint}", extra=log_data)

def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or mask sensitive data from logs"""
    sensitive_keys = ['password', 'api_key', 'token', 'secret', 'key']
    sanitized = {}
    
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        else:
            sanitized[key] = value
    
    return sanitized

# Initialize logging on module import
def init_logging():
    """Initialize logging with environment-based configuration"""
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    config_path = os.getenv("LOGGING_CONFIG_PATH")
    
    setup_logging(
        config_path=config_path,
        log_level=log_level,
        environment=environment
    )

# Auto-initialize when module is imported
init_logging()