from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.database.session import init_db, SessionLocal
from app.seed.seed_data import seed_database
from app.models.merchant import Merchant
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Merchant Liquidity Engine backend...")
    init_db()
    
    # Auto-seed if database is empty
    db = SessionLocal()
    try:
        existing = db.query(Merchant).filter(Merchant.id == "mch_aarav_001").first()
        if not existing:
            logger.info("No merchant records found. Auto-seeding initial sandbox dataset...")
            seed_database(db=db)
        else:
            logger.info(f"Merchant {existing.name} loaded successfully.")
    except Exception as e:
        logger.error(f"Error during startup data verification: {e}")
    finally:
        db.close()
        
    yield
    logger.info("Shutting down Merchant Liquidity Engine backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Merchant Liquidity Engine - Optimize what a transaction does to the business",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^http:\/\/(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "path": request.url.path,
        },
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "engine": "Merchant Liquidity Engine",
        "tagline": "Optimize what a transaction does to the business.",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
