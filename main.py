from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pathlib import Path
import traceback

from core.config import settings, BASE_DIR
from core.error_handler import AppException, log_error

# Import Routers
from routers import auth, vendors, invoices, admin, general, reports, monitoring, settings as settings_router, tax_documents

from core.dependencies import get_db
from models.database import init_db

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    init_db()

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development/testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include Routers
app.include_router(general.router)
app.include_router(auth.router)
app.include_router(vendors.router)
app.include_router(invoices.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(monitoring.router)
app.include_router(settings_router.router)
app.include_router(tax_documents.router)

# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    log_error(exc, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_code": exc.error_code, "message": exc.message}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle 422 Validation Errors with JSON response"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(exc, request.url.path)
    
    # AI Monitoring Sentinel: Capture Error in DB
    try:
        from models.database import SessionLocal
        from models.error_log import ErrorLog
        from core.dependencies import get_current_user
        
        db = SessionLocal()
        
        # Try to get user context if possible
        user_id = None
        try:
            user = await get_current_user(request)
            user_id = user.get("id")
        except:
            pass
            
        error_entry = ErrorLog(
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
            endpoint=request.url.path,
            method=request.method,
            user_id=user_id
        )
        db.add(error_entry)
        db.commit()
        db.close()
    except Exception as e:
        print(f"FAILED TO LOG TO ERROR_LOG: {e}")

    return JSONResponse(
        status_code=500,
        content={"success": False, "error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
