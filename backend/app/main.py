from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, users, properties, profile, messages
from app.database import engine, Base

# Import the new route modules
from app.routes import image_analysis, chat_ai, recommendations
from app.routes import floor_plans, ml_pipeline, architectural_style

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="uninest API",
    description="API for uninest - Personalized Housing Recommendation System with Architectural Analysis",
    version="0.2.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

# Property and profile routes
app.include_router(
    properties.router,
    prefix=f"{settings.API_V1_STR}/properties",
    tags=["Properties"]
)

app.include_router(
    profile.router,
    prefix=f"{settings.API_V1_STR}/profile",
    tags=["User Profiles"]
)

# Recommendation-related routes:
app.include_router(
    image_analysis.router,
    prefix=f"{settings.API_V1_STR}/images",
    tags=["Image Analysis"]
)

app.include_router(
    chat_ai.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["Chat"]
)

app.include_router(
    recommendations.router,
    prefix=f"{settings.API_V1_STR}/recommendations",
    tags=["Recommendations"]
)

# NEW ARCHITECTURAL ROUTES
app.include_router(
    floor_plans.router,
    prefix=f"{settings.API_V1_STR}/floor-plans",
    tags=["Floor Plan Analysis"]
)

app.include_router(
    ml_pipeline.router,
    prefix=f"{settings.API_V1_STR}/ml-pipeline",
    tags=["ML Data Pipeline"]
)

app.include_router(
    architectural_style.router,
    prefix=f"{settings.API_V1_STR}/architectural-styles",
    tags=["Architectural Style Analysis"]
)

app.include_router(
    messages.router,
    prefix=f"{settings.API_V1_STR}/messages",
    tags=["Messages"]
)

@app.get("/")
def root():
    """
    Root endpoint - can be used for health checks
    """
    return {
        "message": "Welcome to uninest API",
        "version": "0.2.0",
        "new_features": [
            "Floor plan analysis",
            "Architectural style classification",
            "ML data pipeline for architectural analysis",
            "Construction materials analysis"
        ]
    }
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # Port 8000 is an example