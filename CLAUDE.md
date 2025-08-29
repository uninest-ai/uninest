# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UniNest is a full-stack web application for student housing recommendations near CMU, featuring AI-powered chat assistance, image analysis, and roommate matching.

**Architecture**: 
- **Backend**: FastAPI (Python) with PostgreSQL, deployed via Docker
- **Frontend**: React + Vite with Tailwind CSS 
- **AI Integration**: OpenAI GPT-4 for chat and image analysis
- **Infrastructure**: AWS (EC2, RDS, S3) with Docker Compose orchestration

## Development Commands

### Docker (Primary Development Method)
```bash
# Build and start all services
docker-compose build
docker-compose up

# Rebuild and restart (when dependencies change)
docker-compose down && docker-compose up -d --build

# View logs
docker-compose logs
docker-compose logs backend  # specific service logs
docker-compose logs frontend

# Stop services
docker-compose down
```

### Backend (FastAPI)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Run tests
pytest
pytest tests/test_specific.py  # single test file
pytest -v  # verbose output
```

### Frontend (React + Vite)
```bash
cd frontend/housing-web

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Code Architecture

### Backend Structure (`/backend/app/`)
- **`main.py`**: FastAPI application setup, CORS, and router inclusion
- **`models.py`**: SQLAlchemy ORM models (User, Property, TenantProfile, etc.)
- **`database.py`**: Database connection and session management
- **`auth.py`**: JWT authentication and password hashing
- **`config.py`**: Environment configuration via Pydantic Settings
- **`routes/`**: API endpoint definitions organized by feature
  - `auth.py`: Authentication endpoints
  - `properties.py`: Property management
  - `recommendations.py`: ML-powered recommendation engine
  - `chat_ai.py`: OpenAI chat integration
  - `image_analysis.py`: OpenAI Vision API integration
- **`services/`**: Business logic layer
  - `chat_service.py`: Chat conversation management
  - `image_analysis.py`: Image processing and preference extraction
  - `storage_service.py`: AWS S3 integration
  - `ml_data_pipeline.py`: Recommendation algorithm implementation

### Frontend Structure (`/frontend/housing-web/src/`)
- **`App.jsx`**: Main application component with routing
- **`api.js`**: Axios configuration and API client
- **`config.js`**: Frontend configuration (API base URL, etc.)
- **`components/ProtectedRoute.jsx`**: Route authentication wrapper
- **`pages/`**: Page components for different routes
  - Authentication: `login.jsx`, `register.jsx`
  - User profiles: `profile.jsx`, `tenant-profile.jsx`, `landlord-profile.jsx`
  - Core features: `recommendation.jsx`, `chat.jsx`, `property-detail.jsx`

### Database Models
Key relationships:
- **User**: Base model with `user_type` ('tenant'/'landlord')
- **TenantProfile/LandlordProfile**: Extended user information
- **Property**: Housing listings with location, pricing, amenities
- **UserPreference**: Extracted preferences from chat/image analysis
- **Message**: In-app messaging system
- Many-to-many relationships: `roommate_preferences`, `property_preferences`

## Environment Configuration

Required environment variables (create `.env` in project root):
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Authentication
SECRET_KEY=your-secret-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name

# External APIs
RAPIDAPI_KEY=your-rapidapi-key

# Admin
ADMIN_SECRET=your-admin-secret

# Frontend (for Docker builds)
VITE_API_BASE_URL=http://localhost:8000
```

## Testing

### Backend Tests
- **Framework**: pytest with SQLAlchemy test fixtures
- **Database**: In-memory SQLite for test isolation
- **Location**: `/backend/tests/`
- **Configuration**: `conftest.py` handles test database setup and dependency injection
- **Coverage**: Authentication, user management, property operations, recommendations

### Test User Credentials
```json
{
  "email": "user0@example.com",
  "username": "user0", 
  "user_type": "tenant",
  "password": "User0000"
}
```

## AI Integration Patterns

### Chat System
- Uses OpenAI GPT-4 for natural language preference extraction
- Conversation context maintained in database
- Preference labels automatically extracted and stored in `UserPreference` model

### Image Analysis
- OpenAI Vision API analyzes uploaded home images
- Extracts architectural style, space characteristics, mood preferences
- Results integrated into recommendation scoring algorithm

### Recommendation Engine
Property scoring algorithm (located in `services/ml_data_pipeline.py`):
- Budget compatibility (30%)
- Location proximity (30%) 
- Property type match (20%)
- Bedroom/bathroom requirements (20%)

Roommate scoring algorithm:
- Budget alignment (30%)
- Location preferences (30%)
- Lifestyle compatibility (40%)

## Development Notes

- **Authentication**: JWT tokens with FastAPI security dependencies
- **Database**: PostgreSQL in production, SQLite for testing
- **File Storage**: AWS S3 for property images and user uploads
- **API Documentation**: Auto-generated at `/docs` (FastAPI/OpenAPI)
- **CORS**: Configured for localhost development and production domains
- **Deployment**: Docker containers on AWS EC2 with RDS database

## Admin Operations

Reset database and fetch sample properties:
```bash
curl -X POST "http://3.14.150.166:8000/api/v1/admin/fetch-real-properties?property_count=5" \
  -H "X-Admin-Key: Admin123456"
```