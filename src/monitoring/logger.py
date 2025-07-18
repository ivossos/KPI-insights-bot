import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import traceback

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and structured output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        super().__init__()
        
    def format(self, record):
        # Create log format
        log_format = "[{asctime}] [{levelname}] [{name}] {message}"
        
        # Add colors if enabled
        if self.use_colors and record.levelname in self.COLORS:
            log_format = f"{self.COLORS[record.levelname]}{log_format}{self.COLORS['RESET']}"
            
        # Set format
        formatter = logging.Formatter(log_format, style='{')
        
        # Add extra fields if available
        if hasattr(record, 'user_id'):
            record.message = f"[User: {record.user_id}] {record.getMessage()}"
        else:
            record.message = record.getMessage()
            
        return formatter.format(record)

class StructuredLogger:
    """Structured logging system for IA Fiscal Capivari"""
    
    def __init__(self, name: str = "ia_fiscal_capivari"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Ensure logs directory exists
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_handler()
        self._setup_json_handler()
        
    def _setup_console_handler(self):
        """Setup console handler with colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter(use_colors=True))
        self.logger.addHandler(console_handler)
        
    def _setup_file_handler(self):
        """Setup rotating file handler"""
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(CustomFormatter(use_colors=False))
        self.logger.addHandler(file_handler)
        
    def _setup_error_handler(self):
        """Setup error-specific handler"""
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomFormatter(use_colors=False))
        self.logger.addHandler(error_handler)
        
    def _setup_json_handler(self):
        """Setup JSON handler for structured logging"""
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "structured.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
        
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
        
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user action"""
        self.info(f"User action: {action}", user_id=user_id, action=action, details=details or {})
        
    def log_system_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log system event"""
        self.info(f"System event: {event_type}", event_type=event_type, details=details or {})
        
    def log_api_request(self, method: str, path: str, user_id: str = None, response_time: float = None, status_code: int = None):
        """Log API request"""
        self.info(f"API {method} {path}", 
                 method=method, 
                 path=path, 
                 user_id=user_id,
                 response_time=response_time,
                 status_code=status_code)
        
    def log_database_query(self, query_type: str, table: str, execution_time: float = None, rows_affected: int = None):
        """Log database query"""
        self.debug(f"Database {query_type} on {table}",
                  query_type=query_type,
                  table=table,
                  execution_time=execution_time,
                  rows_affected=rows_affected)
        
    def log_alert_created(self, alert_id: str, rule_type: str, risk_score: int, affected_records: int):
        """Log alert creation"""
        self.info(f"Alert created: {alert_id}",
                 alert_id=alert_id,
                 rule_type=rule_type,
                 risk_score=risk_score,
                 affected_records=affected_records)
        
    def log_notification_sent(self, notification_type: str, recipient: str, success: bool):
        """Log notification sending"""
        status = "success" if success else "failed"
        self.info(f"Notification {status}: {notification_type} to {recipient}",
                 notification_type=notification_type,
                 recipient=recipient,
                 success=success)
        
    def log_data_processing(self, dataset_id: str, dataset_type: str, records_processed: int, processing_time: float):
        """Log data processing"""
        self.info(f"Data processing completed: {dataset_id}",
                 dataset_id=dataset_id,
                 dataset_type=dataset_type,
                 records_processed=records_processed,
                 processing_time=processing_time)
        
    def log_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """Log exception with context"""
        self.error(f"Exception: {str(exception)}",
                  exception_type=type(exception).__name__,
                  exception_message=str(exception),
                  traceback=traceback.format_exc(),
                  context=context or {})

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_entry[key] = value
                
        return json.dumps(log_entry)

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.metrics = {}
        
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{datetime.now().timestamp()}"
        self.metrics[timer_id] = {
            "operation": operation,
            "start_time": datetime.now(),
            "status": "running"
        }
        return timer_id
        
    def stop_timer(self, timer_id: str, success: bool = True, details: Dict[str, Any] = None):
        """Stop timing an operation"""
        if timer_id in self.metrics:
            metric = self.metrics[timer_id]
            metric["end_time"] = datetime.now()
            metric["duration"] = (metric["end_time"] - metric["start_time"]).total_seconds()
            metric["success"] = success
            metric["details"] = details or {}
            metric["status"] = "completed"
            
            # Log performance metric
            self.logger.info(f"Performance: {metric['operation']} completed in {metric['duration']:.2f}s",
                           operation=metric["operation"],
                           duration=metric["duration"],
                           success=success,
                           details=details)
            
            # Clean up
            del self.metrics[timer_id]
            
    def get_active_timers(self) -> Dict[str, Any]:
        """Get currently active timers"""
        return {k: v for k, v in self.metrics.items() if v["status"] == "running"}
        
    def log_memory_usage(self):
        """Log current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.logger.info("Memory usage",
                           memory_mb=memory_info.rss / 1024 / 1024,
                           memory_percent=process.memory_percent())
        except ImportError:
            self.logger.warning("psutil not available for memory monitoring")
            
    def log_system_resources(self):
        """Log system resource usage"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            self.logger.info("System resources",
                           cpu_percent=cpu_percent,
                           memory_percent=memory.percent,
                           memory_available_mb=memory.available / 1024 / 1024,
                           disk_percent=disk.percent,
                           disk_free_gb=disk.free / 1024 / 1024 / 1024)
                           
        except ImportError:
            self.logger.warning("psutil not available for system monitoring")

class SecurityLogger:
    """Security-focused logging"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        
    def log_auth_attempt(self, user_email: str, success: bool, ip_address: str = None):
        """Log authentication attempt"""
        self.logger.info(f"Authentication {'success' if success else 'failure'}: {user_email}",
                        user_email=user_email,
                        success=success,
                        ip_address=ip_address,
                        security_event="auth_attempt")
        
    def log_permission_denied(self, user_email: str, resource: str, action: str, ip_address: str = None):
        """Log permission denied"""
        self.logger.warning(f"Permission denied: {user_email} tried to {action} {resource}",
                          user_email=user_email,
                          resource=resource,
                          action=action,
                          ip_address=ip_address,
                          security_event="permission_denied")
        
    def log_suspicious_activity(self, user_email: str, activity: str, details: Dict[str, Any] = None):
        """Log suspicious activity"""
        self.logger.warning(f"Suspicious activity: {activity} by {user_email}",
                          user_email=user_email,
                          activity=activity,
                          details=details or {},
                          security_event="suspicious_activity")
        
    def log_data_export(self, user_email: str, export_type: str, record_count: int):
        """Log data export"""
        self.logger.info(f"Data export: {export_type} by {user_email}",
                        user_email=user_email,
                        export_type=export_type,
                        record_count=record_count,
                        security_event="data_export")
        
    def log_configuration_change(self, user_email: str, setting: str, old_value: Any, new_value: Any):
        """Log configuration change"""
        self.logger.info(f"Configuration change: {setting} by {user_email}",
                        user_email=user_email,
                        setting=setting,
                        old_value=str(old_value),
                        new_value=str(new_value),
                        security_event="config_change")

class AlertLogger:
    """Alert-specific logging"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        
    def log_rule_execution(self, rule_type: str, dataset_size: int, alerts_generated: int, execution_time: float):
        """Log rule execution"""
        self.logger.info(f"Rule execution: {rule_type}",
                        rule_type=rule_type,
                        dataset_size=dataset_size,
                        alerts_generated=alerts_generated,
                        execution_time=execution_time)
        
    def log_alert_investigation(self, alert_id: str, user_email: str, status: str, notes: str = None):
        """Log alert investigation"""
        self.logger.info(f"Alert investigation: {alert_id} marked as {status}",
                        alert_id=alert_id,
                        user_email=user_email,
                        status=status,
                        notes=notes)
        
    def log_ai_explanation(self, alert_id: str, explanation_length: int, processing_time: float):
        """Log AI explanation generation"""
        self.logger.info(f"AI explanation generated for alert {alert_id}",
                        alert_id=alert_id,
                        explanation_length=explanation_length,
                        processing_time=processing_time)

# Global logger instance
logger = StructuredLogger()
performance_monitor = PerformanceMonitor(logger)
security_logger = SecurityLogger(logger)
alert_logger = AlertLogger(logger)

# Convenience functions
def log_info(message: str, **kwargs):
    logger.info(message, **kwargs)
    
def log_warning(message: str, **kwargs):
    logger.warning(message, **kwargs)
    
def log_error(message: str, **kwargs):
    logger.error(message, **kwargs)
    
def log_exception(exception: Exception, context: Dict[str, Any] = None):
    logger.log_exception(exception, context)

# Context manager for performance monitoring
class performance_timer:
    """Context manager for timing operations"""
    
    def __init__(self, operation: str, details: Dict[str, Any] = None):
        self.operation = operation
        self.details = details or {}
        self.timer_id = None
        
    def __enter__(self):
        self.timer_id = performance_monitor.start_timer(self.operation)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        if exc_type:
            self.details['exception'] = str(exc_val)
        performance_monitor.stop_timer(self.timer_id, success, self.details)
        
# Decorator for automatic function timing
def timed_function(operation_name: str = None):
    """Decorator to automatically time function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with performance_timer(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator