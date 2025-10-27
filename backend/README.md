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
DATABASE_URL=postgresql://uninest_admin:xxxxxx@db:0000/uninest
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
4. **Build and start all services (backend + frontend + database):** (local & cloud)
  ```
  本地运行（你的电脑）

  # 在你的WSL/本地运行
  cd "/mnt/d/ahYen Workspace/ahYen 
  Work/CMU_academic/MSCD_Y1_2425/17637-WebApps/uninest"

  # 这些命令都是在本地运行，与云端无关
  docker-compose up --build        # 启动本地Docker容器
  docker-compose logs -f backend   # 查看本地容器日志
  - 作用范围：只在你的电脑上
  - 访问地址：http://localhost:8000
  - 数据库：连接到你.env中配置的RDS（远程数据库）

  云端部署（EC2服务器 3.145.189.113）

  # 必须先SSH连接到服务器
  ssh -i your-key.pem ubuntu@3.145.189.113

  # 然后在服务器上运行
  cd /path/to/uninest
  git pull origin main                    # 拉取最新代码
  docker-compose up -d --build           # 在服务器上重新构建
  docker-compose logs -f backend         # 查看服务器容器日志
  - 作用范围：云端服务器
  - 访问地址：http://3.145.189.113:8000
  - 公网用户可以访问

  ---
  完整的更新流程

  步骤1：本地测试（在你电脑上）

  # 在本地项目目录
  cd "/mnt/d/ahYen Workspace/ahYen 
  Work/CMU_academic/MSCD_Y1_2425/17637-WebApps/uninest"

  # 修改代码后，本地测试
  docker-compose up --build

  # 查看日志确认没问题
  docker-compose logs -f backend

  # 测试API是否正常
  curl http://localhost:8000/

  步骤2：提交代码到Git

  git add .
  git commit -m "update backend code"
  git push origin main

  步骤3：SSH到云端服务器更新

  # 连接到EC2
  ssh -i your-key.pem ubuntu@3.145.189.113

  # 进入项目目录
  cd /path/to/uninest

  # 拉取最新代码
  git pull origin main

  # 重新构建并启动
  docker-compose down
  docker-compose up -d --build

  # 查看服务器日志
  docker-compose logs -f backend

  # 退出SSH（Ctrl+C停止查看日志，然后exit）
  exit

  步骤4：验证云端更新成功

  # 在你本地电脑访问云端API
  curl http://3.145.189.113:8000/
  ```

## API Documentation

When the application is running, you can access the interactive Swagger UI documentation at:
- **Local**: `http://localhost:8000/docs`
- **Production**: `http://3.145.189.113:8000/docs`

## Testing

Run the test suite with pytest:
```bash
pytest
pytest -v  # verbose output
pytest tests/test_specific.py  # run specific test file
```

---

## Deployment

The backend is deployed on AWS EC2 with Docker containers.

### Method 1: SSH + Docker Deployment (Recommended)

**Step 1: Commit and push local changes**
```bash
# In project root directory
git add .
git commit -m "update backend code"
git push origin main
```

**Step 2: SSH into EC2 server**
```bash
ssh -i your-key.pem ubuntu@3.145.189.113
```

**Step 3: Pull latest code**
```bash
cd /path/to/uninest
git pull origin main
```

**Step 4: Rebuild and restart containers**
```bash
# Stop existing containers
docker-compose down

# Rebuild backend only (faster if only backend changed)
docker-compose build backend

# Start all services
docker-compose up -d

# Verify successful startup
docker-compose logs -f backend
```

### Method 2: Hot Update (Small Changes Only)

For quick fixes without rebuilding:
```bash
# SSH to server
ssh -i your-key.pem ubuntu@3.145.189.113

# Edit file directly
cd /path/to/uninest/backend
vim app/routes/your_file.py

# Restart backend
docker-compose restart backend
```

### Method 3: CI/CD Automation (Production)

Create `.github/workflows/deploy.yml`:
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

---

## Command Reference

### 🐳 Docker Commands

**Container Management**
```bash
# Check running containers
docker-compose ps

# Start all services
docker-compose up -d

# Start with rebuild
docker-compose up -d --build

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# Fully rebuild and restart
docker-compose down && docker-compose up -d --build
```

**Logs and Debugging**
```bash
# View backend logs (real-time)
docker-compose logs -f backend

# View all service logs
docker-compose logs

# View last 100 lines
docker-compose logs --tail=100 backend

# Enter backend container shell
docker-compose exec backend bash

# Enter database container
docker-compose exec db psql -U uninest_admin -d uninest
```

---

### 🗄️ Database Migration Commands

```bash
# Check current migration version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Apply specific migration
docker-compose exec backend alembic upgrade e1a2b3c4d5e6

# Create new migration (auto-generate from models)
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Check for schema issues
docker-compose exec backend python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
result = db.execute(text('SELECT version_num FROM alembic_version')).fetchone()
print(f'Current migration: {result[0]}')
db.close()
"
```

---

### 🏢 Property Data Management

**Fetch Real Estate Data**
```bash
# Check system status
curl "http://localhost:8000/api/v1/admin/status" \
  -H "X-Admin-Key: Admin123456" | jq

# Fetch properties (auto-creates landlords)
curl -X POST "http://localhost:8000/api/v1/admin/fetch-real-properties?property_count=15" \
  -H "X-Admin-Key: Admin123456" | jq

# Fetch from multiple sources (comprehensive)
curl -X POST "http://localhost:8000/api/v1/admin/fetch-multi-source-properties?property_count=50" \
  -H "X-Admin-Key: Admin123456" | jq

# Manual sync (scheduler logic)
curl -X POST "http://localhost:8000/api/v1/admin/sync/manual?sync_type=incremental" \
  -H "X-Admin-Key: Admin123456" | jq
```

**Verify Data**
```bash
# Check total properties
curl "http://localhost:8000/api/v1/properties" | jq 'length'

# Get specific property details
curl "http://localhost:8000/api/v1/properties/1" | jq

# View property description with links
curl "http://localhost:8000/api/v1/properties/1" | jq '.description'

# List all landlords
curl "http://localhost:8000/api/v1/admin/landlords" \
  -H "X-Admin-Key: Admin123456" | jq

# List API-created landlords
curl "http://localhost:8000/api/v1/admin/real-landlords" \
  -H "X-Admin-Key: Admin123456" | jq
```

**Data Analytics**
```bash
# Property sources report
curl "http://localhost:8000/api/v1/admin/property-sources" \
  -H "X-Admin-Key: Admin123456" | jq

# Property links report (Realtor.com, Zillow, etc.)
curl "http://localhost:8000/api/v1/admin/property-links" \
  -H "X-Admin-Key: Admin123456" | jq

# Get detailed property information
curl "http://localhost:8000/api/v1/admin/property-details/123" \
  -H "X-Admin-Key: Admin123456" | jq
```

---

### 🔍 BM25 Full-Text Search

**Basic Search**
```bash
# Search for apartments
curl "http://localhost:8000/api/v1/properties/search?q=apartment&limit=5" | jq

# Multi-word search
curl "http://localhost:8000/api/v1/properties/search?q=modern+2BR+near+campus" | jq

# Search with minimum relevance score
curl "http://localhost:8000/api/v1/properties/search?q=spacious&limit=10&min_score=0.1" | jq

# Neighborhood search
curl "http://localhost:8000/api/v1/properties/search?q=Squirrel+Hill" | jq
```

**Test BM25 Search (Python)**
```bash
# Run comprehensive BM25 test
docker-compose exec backend python test_bm25.py

# Quick search test
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.services.search_service import bm25_search_properties

db = SessionLocal()
results = bm25_search_properties(db, 'apartment', limit=5)
for prop, score in results:
    print(f'{prop.title} - Score: {score:.4f}')
db.close()
"
```

**Verify BM25 Components**
```bash
# Check search_vector column exists
docker-compose exec backend python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
result = db.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \'properties\' AND column_name = \'search_vector\'')).fetchone()
print('✅ search_vector exists!' if result else '❌ Column not found')
db.close()
"

# Check GIN index
docker-compose exec backend python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
result = db.execute(text('SELECT indexname FROM pg_indexes WHERE tablename = \'properties\' AND indexname = \'idx_properties_search_vector\'')).fetchone()
print('✅ GIN index exists!' if result else '❌ Index not found')
db.close()
"
```

---

### 🧹 Database Maintenance

```bash
# Reset database (WARNING: deletes all data)
curl -X DELETE "http://localhost:8000/api/v1/admin/reset-database?confirm=RESET_ALL_DATA" \
  -H "X-Admin-Key: Admin123456" | jq

# Clean up old properties (30+ days)
curl -X DELETE "http://localhost:8000/api/v1/admin/cleanup-properties/1?older_than_days=30" \
  -H "X-Admin-Key: Admin123456" | jq

# Migrate API images to PropertyImage table
curl -X POST "http://localhost:8000/api/v1/admin/migrate-images" \
  -H "X-Admin-Key: Admin123456" | jq
```

---

### 🔧 Development & Debugging

**Health Checks**
```bash
# Check API is running
curl http://localhost:8000/

# Check API docs
curl http://localhost:8000/docs

# Verify database connection
docker-compose exec backend python -c "
from app.database import SessionLocal
db = SessionLocal()
print('✅ Database connected successfully')
db.close()
"
```

**Interactive Testing**
```bash
# Python shell in container
docker-compose exec backend python

# Run specific service test
docker-compose exec backend python -c "
from app.services.realtor16_fetcher import Realtor16Fetcher
import os
api_key = os.getenv('RAPIDAPI_KEY')
print(f'API Key configured: {bool(api_key)}')
"
```

---

## Server Information
连接command:
```
ssh -i ~/.ssh/uninest_mykey_new.pem ec2-user@3.145.189.113
```

- **EC2 IP**: 3.145.189.113
- **Backend Port**: 8000
- **Frontend Port**: 80
- **Database**: PostgreSQL RDS (production) / Docker container (local)
- **Admin Key**: Admin123456 (stored in `ADMIN_SECRET` env variable)

**Endpoints:**
- Local API: `http://localhost:8000`
- Production API: `http://3.145.189.113:8000`
- Local Docs: `http://localhost:8000/docs`
- Production Docs: `http://3.145.189.113:8000/docs`

---

## Test Credentials

**Default Test User:**
```json
{
  "email": "test0@example.com",
  "username": "testuser0",
  "password": "String123",
  "user_type": "tenant"
}
```

**Admin Access:**
- Header: `X-Admin-Key: Admin123456`
- Required for: `/api/v1/admin/*` endpoints

---

## Important Notes

1. **Environment Variables**: Ensure `.env` file contains all required variables on both local and server
2. **Database Migrations**: Always run `alembic upgrade head` after model changes
3. **Ports**: Backend (8000), Frontend (80), PostgreSQL (5432)
4. **Health Check**: Visit `/docs` endpoint to verify API is running
5. **BM25 Search**: Requires migration `e1a2b3c4d5e6` to be applied
6. **API Rate Limits**: RapidAPI free tier has usage limits - monitor calls

## Contributors

- Chia Hui Yen (huiyenc) - main
- Mathilda Chen (liyingch)
- Yiqi Cheng (yiqic2)