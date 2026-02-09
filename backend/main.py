"""
TrustLens AI - Contract Review Assistant Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

# Import routers
from api import rule_routes, document_routes


class Settings(BaseSettings):
    """Application settings"""

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    database_url: str = "sqlite:///./trustlens.db"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI(
    title="TrustLens AI",
    description="合同审核助手 API",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rule_routes.router, prefix="/api")
app.include_router(document_routes.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TrustLens AI - Contract Review Assistant",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "rules": "/api/rules",
            "documents": "/api/documents",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
