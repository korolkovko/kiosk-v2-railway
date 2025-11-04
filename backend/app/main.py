# main.py
# FastAPI application main entry point

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .api import api_router
from .config import get_settings
from .database import engine
from .database.models import Base
import textwrap

settings = get_settings()
print("📦 DB URL:", os.getenv("DATABASE_URL"))

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="KIOSK Application Backend API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# ============================================
# STATIC FILE MOUNTS
# ============================================

# Mount uploads directory
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ============================================
# MEDIA ASSETS MOUNT (Config-Only Solution)
# ============================================
# Purpose: Serve media files (images, videos) for kiosk frontend
#          Frontend cannot access file:// URLs due to browser security,
#          so backend serves files via HTTP from configurable directory
#
# Configuration: Set MEDIA_PATH in backend/.env
#   - Development: "./media" or "../frontend/apps/kiosk/public"
#   - Production: "/var/kiosk/media"
#
# Future Enhancement: When implementing full CMS, replace this with:
#   - Storage provider abstraction (backend/app/services/storage/)
#   - Upload endpoints (POST /api/v1/admin/upload/...)
#   - Database URL tracking
#   - Image processing (resize, optimize)
#
# Note: This is temporary read-only file serving. No business logic,
#       no upload handling - just serving files from configured path.
# ============================================
media_dir = settings.MEDIA_PATH
if os.path.exists(media_dir):
    app.mount("/media", StaticFiles(directory=media_dir), name="media")
    logger.info(f"✅ Media directory mounted: {media_dir} -> /media")
else:
    logger.warning(f"⚠️  Media directory not found: {media_dir}")
    logger.warning(f"⚠️  Set MEDIA_PATH in backend/.env to serve media files")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting KIOSK Application Backend")
    
    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down KIOSK Application Backend")


@app.get("/")
async def root():
    return {"message": "KIOSK Application Backend API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

import textwrap
def log_envs():
    env_items = sorted(os.environ.items())
    formatted = "\n".join(f"{key}={value}" for key, value in env_items)

    message = textwrap.indent(formatted, "    ")

    wrapped_message = "\n".join([
        "-" * 80, "ENVIRONMENT VARIABLES (BEGIN):", "-" * 80,
        message,
        "-" * 80, "ENVIRONMENT VARIABLES (END):", "-" * 80
    ])

    # Log as one INFO record
    print("\n%s", wrapped_message)
print(f"{__name__} this is the module name")
print(settings)
log_envs()

if __name__ == "__main__":
    
    import uvicorn
    log_envs()

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )