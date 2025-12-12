"""USB Drop Campaign Manager - FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, campaigns, profiles, drives, tokens, webhooks, alerts, generate, reports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting USB Drop Campaign Manager...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Create initial admin user if not exists
    from app.services.auth_service import create_initial_admin
    create_initial_admin()

    yield

    # Shutdown
    logger.info("Shutting down USB Drop Campaign Manager...")


# Create FastAPI app
app = FastAPI(
    title="USB Drop Campaign Manager",
    description="API for managing USB drop penetration testing campaigns with CanaryTokens",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"https://app.{settings.canary_domain}",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(drives.router, prefix="/api/drives", tags=["Drives"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["Tokens"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(generate.router, prefix="/api/generate", tags=["Content Generation"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "USB Drop Campaign Manager",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
