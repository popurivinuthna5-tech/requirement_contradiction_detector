import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR, ENVIRONMENT
from app.database import init_db
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.requirements import router as requirements_router
from app.api.conflicts import router as conflicts_router
from app.api.settings import router as settings_router
from app.api.demo import router as demo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("requirement_analyzer")

app = FastAPI(
    title="Requirement Conflict & Overlap Analyzer API",
    description="Enterprise AI system for identifying contradictory, conflicting, duplicate, and semantically overlapping requirements.",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Database initialized successfully.")

# Global safe error handler (prevents exposing internal tracebacks)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error handling {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred during requirement processing. Please try again or contact support."}
    )

# Include API routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(requirements_router)
app.include_router(conflicts_router)
app.include_router(settings_router)
app.include_router(demo_router)

# Healthcheck endpoint
@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "Requirement Conflict & Overlap Analyzer"}

# Mount Static Files for frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If accessing an API route that didn't match, return 404
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        
        # Fallback to index.html for Single Page Application
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"detail": "Frontend files not found"})

if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
