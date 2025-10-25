# uninest Backend

Backend service for uninest - A Personalized Housing Recommendation System near CMU.

## Features

- **User Authentication**: Register and login with JWT-based authentication
- **Property Management**: Create, update, view, and delete property listings
- **User Profiles**: Separate profiles for tenants and landlords
- **Preference Tracking**: Multiple ways to collect user preferences:
  - AI-powered chat interface
  - Image analysis for visual preferences
  - Direct preference input
- **Personalized Recommendations**: 
  - Property recommendations based on user preferences
  - Roommate matching for compatible housing partners
- **Messaging System**: Direct communication between users
- **Image Management**: Upload and analyze property images

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **AI Services**:
  - OpenAI integration for chat analysis and preference extraction
  - Image analysis for property characteristics and user preferences
- **Cloud Services**:
  - AWS S3 for image storage
  - AWS EC2 for deployment

## Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Application configuration
│   ├── database.py           # Database connection
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas for validation
│   ├── auth.py               # Authentication utilities
│   ├── routes/               # API route handlers
│   │   ├── auth.py           # Authentication routes
│   │   ├── users.py          # User management
│   │   ├── properties.py     # Property listing management
│   │   ├── profile.py        # User profile management
│   │   ├── messages.py       # User messaging
│   │   ├── chat_ai.py        # AI chat functionality
│   │   ├── image_analysis.py # Image analysis
│   │   └── recommendations.py # Recommendation endpoints
│   ├── services/             # Business logic services
│   │   ├── chat_service.py   # AI chat service
│   │   ├── image_analysis.py # Image analysis service
│   │   ├── map_service.py    # Map and location service
│   │   └── storage_service.py # S3 storage service
│   └── recommendations.py    # Recommendation algorithms
```

## API Endpoints

The API is organized into the following groups:

- **Authentication**: `/api/v1/auth`
- **Users**: `/api/v1/users`
- **Properties**: `/api/v1/properties`
- **User Profiles**: `/api/v1/profile`
- **Messages**: `/api/v1/messages`
- **Chat**: `/api/v1/chat`
- **Image Analysis**: `/api/v1/images`
- **Recommendations**: `/api/v1/recommendations`

## Setup and Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- AWS account (for S3 image storage)
- OpenAI API key

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://uninest_admin:4Iie-ZDx1n.]E*NWG-kf3~#R~)-z@uninest-db.c9aes4a2k2n8.us-east-2.rds.amazonaws.com:5432/uninest
SECRET_KEY=your-secret-key-for-jwt
ACCESS_TOKEN_EXPIRE_MINUTES=30
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-2
OPENAI_API_KEY=your-openai-api-key
```

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## API Documentation

When the application is running, you can access the Swagger UI documentation at:
`http://localhost:8000/docs` or `http://ip-address:8000/docs`

## Testing

Run tests with pytest:
```
pytest
```

## Deployment

The backend is deployed on AWS EC2

Based on your project configuration, here is a complete process for deploying local backend code changes to an EC2 public server:

### Method 1: SSH + Docker Deployment (Recommended)

1. **Commit code changes locally and push to Git:**
   ```bash
   # In the project root directory
   git add .
   git commit -m "update backend code"
   git push origin main
   ```

2. **SSH into your EC2 server:**
   ```bash
   ssh -i your-key.pem ubuntu@3.145.189.113
   ```

3. **Pull the latest code on the EC2 server:**
   ```bash
   cd /path/to/uninest  # Navigate to your project directory
   git pull origin main
   ```

4. **Rebuild and start Docker containers:**
   ```bash
   # Stop existing containers
   docker-compose down

   # Rebuild backend only (faster if only backend code changes)
   docker-compose build backend

   # Start all services
   docker-compose up -d

   # Check logs to confirm successful startup
   docker-compose logs backend
   ```

### Method 2: Hot Update (For Small Changes Only)

If you only made a small change, you can edit directly on the server:

```bash
# SSH to the server
ssh -i your-key.pem ubuntu@3.145.189.113

# Edit the file
cd /path/to/uninest/backend
vim app/routes/your_file.py

# Restart backend container
docker-compose restart backend
```

### Method 3: CI/CD Automation (Recommended for Production)

Create `.github/workflows/deploy.yml` in your project root:

```yaml
name: Deploy to EC2

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: 3.145.189.113
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /path/to/uninest
            git pull origin main
            docker-compose down
            docker-compose up -d --build
```

## Useful Command Reference

- Check running containers:
  ```bash
  docker-compose ps
  ```

- Check backend logs:
  ```bash
  docker-compose logs -f backend
  ```

- Restart only the backend (without rebuilding):
  ```bash
  docker-compose restart backend
  ```

- Fully rebuild and start:
  ```bash
  docker-compose down && docker-compose up -d --build
  ```

- Enter the backend container for debugging:
  ```bash
  docker-compose exec backend bash
  ```

## Notes

1. **Environment Variables:** Make sure the `.env` file on the server contains all necessary environment variables.
2. **Database Migrations:** If you changed models, don’t forget to run migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
3. **Ports:** Backend is running on port 8000, Frontend on port 80.
4. **Health Check:** After deployment, visit [http://3.145.189.113:8000/docs](http://3.145.189.113:8000/docs) to confirm the API is working.

## Your Server Information

- **EC2 IP:** 3.145.189.113
- **Backend port:** 8000
- **Frontend port:** 80
- **Database:** PostgreSQL (in container) or RDS (production)

Do you already have your server's SSH private key? If so, I can help you write a deployment script to automate this process.


## Contributors

- Chia Hui Yen (huiyenc) - main
- Mathilda Chen (liyingch)
- Yiqi Cheng (yiqic2)