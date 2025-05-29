from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, users, properties, profile, messages
from app.database import engine, Base

from app.routes import image_analysis, chat_ai, recommendations
from app.routes import admin_sync

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HorizonHome API",
    description="API for HorizonHome - Personalized Housing Recommendation System",
    version="0.1.0"
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

# app.include_router(
#     map.router,
#     prefix=f"{settings.API_V1_STR}/map",
#     tags=["Map"]
# )

@app.get("/")
def root():
    """
    Root endpoint - can be used for health checks
    """
    return {"message": "Welcome to HorizonHome API"}

app.include_router(
    messages.router,
    prefix=f"{settings.API_V1_STR}/messages",
    tags=["Messages"]
)

app.include_router(
    admin_sync.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Admin Management"]
)