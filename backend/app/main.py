from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, users, properties, profile, messages
from app.database import engine, Base

from app.routes import image_analysis, chat_ai, recommendations
from app.routes import floor_plans, ml_pipeline, architectural_style

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="uninest API",
    description="API for uninest - Personalized Housing Recommendation System with Architectural Analysis",
    version="0.2.0",
    docs_url=f"{settings.API_V1_STR}/docs",  # 例如，如果 settings.API_V1_STR 是 "/api/v1"，这里就是 "/api/v1/docs"
    redoc_url=f"{settings.API_V1_STR}/redoc", # 例如 "/api/v1/redoc"
    openapi_url=f"{settings.API_V1_STR}/openapi.json" # 例如 "/api/v1/openapi.json"
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
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

# New property and profile routes
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

# For recommendations:

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
    return {"message": "Welcome to HorizonHome API"}