"""
Centralized error handling and logging for the NVS Vendor Portal.
Production-hardened with log rotation, request IDs, and proper traceback logging.
"""
import logging
import traceback
import inspect
import uuid
from datetime import datetime
from pathlib import Path
from functools import wraps
from logging.handlers import TimedRotatingFileHandler
from fastapi import Request
from fastapi.responses import JSONResponse

# Create logs directory
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging with rotation
logger = logging.getLogger("NVS_Portal")
logger.setLevel(logging.INFO)

# Formatter
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

# Rotating file handler (daily rotation, keep 30 days)
file_handler = TimedRotatingFileHandler(
    LOG_DIR / "app.log",
    when="midnight",
    backupCount=30,
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
file_handler.suffix = "%Y%m%d"

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Add handlers (avoid duplicates)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

class AppException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(AppException):
    """Validation errors (bad input data)."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class AuthenticationError(AppException):
    """Authentication failures."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)

class BadRequestError(AppException):
    """Bad Request errors."""
    def __init__(self, message: str):
        super().__init__(message, "BAD_REQUEST", 400)

class NotFoundError(AppException):
    """Resource not found."""
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)

class ServiceError(AppException):
    """External service errors (SMS, Email, etc.)."""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service} error: {message}", "SERVICE_ERROR", 503)

def log_error(error: Exception, context: str = "", request_id: str = ""):
    """Log error with full traceback at ERROR level."""
    rid_prefix = f"[{request_id}] " if request_id else ""
    logger.error(f"{rid_prefix}[{context}] {str(error)}")
    
    tb = traceback.format_exc()
    logger.error(f"{rid_prefix}[{context}] Traceback:\n{tb}")

    # DEBUG: Write to trace file
    try:
        with open("debug_trace.txt", "a") as f:
            f.write(f"\n\n--- ERROR {datetime.now()} ---\n")
            f.write(f"Error: {str(error)}\n")
            f.write(tb)
    except:
        pass

def log_info(message: str, context: str = "", request_id: str = ""):
    """Log info message."""
    rid_prefix = f"[{request_id}] " if request_id else ""
    logger.info(f"{rid_prefix}[{context}] {message}")

def log_warning(message: str, context: str = "", request_id: str = ""):
    """Log warning message."""
    rid_prefix = f"[{request_id}] " if request_id else ""
    logger.warning(f"{rid_prefix}[{context}] {message}")

async def request_id_middleware(request: Request, call_next):
    """Middleware to add request correlation ID."""
    request_id = str(uuid.uuid4())[:8]  # Short ID for readability
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware for FastAPI.
    Catches all unhandled exceptions and returns proper JSON responses.
    """
    request_id = getattr(request.state, 'request_id', '')
    try:
        response = await call_next(request)
        return response
    except AppException as e:
        log_error(e, request.url.path, request_id)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "request_id": request_id
            }
        )
    except Exception as e:
        log_error(e, request.url.path, request_id)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id
            }
        )

def safe_api_call(func):
    """
    Decorator for API endpoints to handle errors gracefully.
    Supports both sync and async functions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except AppException:
            raise
        except Exception as e:
            log_error(e, func.__name__)
            raise AppException(str(e), "API_ERROR", 500)
    return wrapper

