from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import traceback
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.services.yolo_service import YOLOv8Service
from app.routers import detect, logs, models, health

# Global variable to track model loading
model_loaded = False

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Initialize YOLOv8 model at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handler."""
    global model_loaded
    
    # Startup
    logger.info("🚀 Starting application...")
    
    # Create database tables
    try:
        logger.info("📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
    
    # Load YOLOv8 model
    try:
        logger.info("🤖 Loading YOLOv8 model...")
        yolo_service = YOLOv8Service()
        model_info = yolo_service.get_model_info()
        logger.info(f"✅ YOLOv8 model loaded successfully: {model_info}")
        model_loaded = True
    except Exception as e:
        logger.error(f"❌ Failed to load YOLOv8 model: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        model_loaded = False
    
    yield
    
    # Shutdown
    logger.info("⏹️  Shutting down application...")


# Create FastAPI app with proper error handling
try:
    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
    )
    
    # Attach rate limiter to app
    app.state.limiter = limiter
except Exception as e:
    logger.error(f"Failed to create FastAPI app: {str(e)}")
    raise


# Rate Limit Exception Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(f"⚠️  Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

# Add security middleware BEFORE other middleware
# Trusted Host Middleware - prevent Host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_ORIGINS,
    www_redirect=True,
)

# GZIP Compression Middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# CORS Middleware - with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
    max_age=600,  # 10 minutes - cache preflight requests
)
logger.info(f"✅ CORS configured for origins: {settings.ALLOWED_ORIGINS}")


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Prevent content type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS - only in production
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            f"max-age={settings.SECURE_HSTS_SECONDS}; "
            f"includeSubDomains; preload"
        )
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none'"
    )
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - do not expose internal details."""
    logger.warning(f"Validation error on {request.url}: {exc.error_count()} errors")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "error_count": exc.error_count(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - do NOT expose internal errors in production."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # In production, do not expose error details
    if settings.DEBUG:
        detail = str(exc)
    else:
        detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


# Include routers
try:
    app.include_router(health.router)
    app.include_router(detect.router)
    app.include_router(logs.router)
    app.include_router(models.router)
    logger.info("✅ All routers registered")
except Exception as e:
    logger.error(f"Failed to register routers: {str(e)}")
    raise


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "🎯 Real-Time Object Detection API",
        "version": settings.API_VERSION,
        "status": "ready" if model_loaded else "model loading...",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/status")
async def status():
    """Get application status."""
    return {
        "api": "running",
        "model": "loaded" if model_loaded else "not loaded",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting API server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
