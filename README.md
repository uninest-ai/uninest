# UniNest - Student Housing 🏠
**Team**: Chia Hui Yen (huiyenc), Mathilda Chen (liyingch), Yiqi Cheng (yiqic2)

**Project Highlight**: A personalized housing recommendation system near CMU that leverages AI-powered image analysis, natural language processing, and advanced matching algorithms to connect students with their ideal homes and compatible roommates.

## 🏗️ Project Overview

UniNest is a comprehensive platform designed specifically for the CMU student community, offering intelligent property and roommate recommendations through multiple interaction modalities including chat-based preference extraction, image analysis, and traditional filtering.

### 🌟 Key Features

- **🤖 AI-Powered Chat Assistant**: Natural language preference extraction for housing requirements
- **📸 Image Analysis**: Upload ideal home images to automatically extract housing preferences  
- **🏘️ Smart Property Recommendations**: Advanced matching algorithms considering budget, location, and lifestyle preferences
- **👥 Roommate Matching**: Compatibility scoring based on lifestyle preferences and housing requirements
- **💬 In-App Messaging**: Direct communication between tenants, landlords, and potential roommates
- **📱 Responsive Design**: Seamless experience across desktop and mobile devices

## 🔧 Tech Stack

**Backend**:
- FastAPI (Python web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- JWT Authentication
- OpenAI GPT-4 (Chat & Image Analysis)
- AWS S3 (Image Storage)

**Frontend**:
- React with TypeScript
- Next.js
- Tailwind CSS
- Axios (API communication)

**Infrastructure**:
- AWS EC2 (Backend hosting)
- AWS RDS (Database)
- Docker (Containerization)

## 🎯 Recommendation Logic

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────►│  Auth Service   │────►│  User Profile   │
│ (Chat/Image/UI) │     │  Verification   │     │  Retrieval      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User/Property  │     │ User Preference │     │  Tenant/Landlord│
│    Database     │◄───►│    Extraction   │◄────│  Profile Check  │
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Score Calculator│     │Feature Matching │     │ Property/User   │
│ PROPERTY:       │     │ROOMMATE:        │     │   Collection    │
│ • Budget (30%)  │────►│ • Budget (30%)  │────►│                 │
│ • Location (30%)│     │ • Location (30%)│     │                 │
│ • Type (20%)    │     │ • Lifestyle(40%)│     │                 │
│ • Bed/Bath (20%)│     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └────────┬────────┘
        │                                                │
        └────────────────────┬───────────────────────────┘
                             │
                             ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Sort Results   │     │ Top-N Selection │     │   API Response  │
│  by Score       │────►│ (Limit Filter)  │────►│   Formatting    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.9+ (for local backend development)

## 🎨 User Interface Screenshots

### Homepage & Navigation
![Homepage Screenshot](screenshots/homepage.png)
*Clean, intuitive homepage with easy navigation for students*

### AI-Powered Property Recommendations
![Property Recommendations](screenshots/recommendations.png)
*Personalized property recommendations with match scores and detailed information*

### Chat Assistant for Preference Extraction
![Chat Assistant](screenshots/chat.png)
*Natural language chat interface that learns your housing preferences*

### Image Analysis Feature
![Image Analysis](screenshots/image-analysis.png)
*Upload photos of your dream home and let AI extract your preferences*

### Roommate Matching
![Roommate Matching](screenshots/roommate-matching.png)
*Find compatible roommates based on lifestyle and housing preferences*

### Property Details & Messaging
![Property Details](screenshots/property-details.png)
*Detailed property information with direct messaging to landlords*

## 🧠 AI Features Deep Dive
### Chat-Based Preference Extraction
The AI chat assistant uses OpenAI's GPT-4 to understand natural language descriptions of housing preferences and automatically categorizes them into:
- **Property preferences**: Type, bedrooms, bathrooms, amenities
- **Location preferences**: Neighborhood, distance to campus, transportation
- **Lifestyle preferences**: Noise level, roommate preferences, study space needs

### Image Analysis
Using OpenAI's Vision API, the system can analyze uploaded images to extract:
- **Architectural style**: Modern, traditional, industrial, etc.
- **Space characteristics**: Open concept, cozy, minimalist
- **Key features**: Hardwood floors, large windows, outdoor space
- **Mood and ambiance**: Bright, warm, sophisticated

## 🔮 Future Enhancements

### Short-term Goals
- [ ] Real-time chat with WebSocket support
- [ ] Advanced map integration with property clusters
- [ ] Push notifications for new matches
- [ ] Enhanced mobile responsiveness

### Medium-term Goals
- [ ] Mobile app development (React Native)
- [ ] Machine learning model improvements
- [ ] Social features and user reviews
- [ ] Integration with external property APIs (Zillow, Apartments.com)

### Long-term Vision
- [ ] Virtual property tours using VR/AR
- [ ] Blockchain-based rental agreements
- [ ] IoT integration for smart property management
- [ ] Expansion to other university communities

## 🙋‍♂️ Support & Contact

For questions, bug reports, or feature requests:

**Development Team**:
- **Chia Hui Yen** (huiyenc@andrew.cmu.edu) - Backend & AI Integration
- **Mathilda Chen** (liyingch@andrew.cmu.edu) - Frontend & Product Owner
- **Yiqi Cheng** (yiqic2@andrew.cmu.edu) - DevOps & Cloud Infrastructure

**Project Links**:
- 🌐 **Live Demo**: [UniNest Application](http://3.145.189.113)


---
## Personal notes:
### Usage:
```
# Connect ubuntu
ssh -v -i "D:\ahYen Workspace\ahYen Work\CMU_academic\MSCD_Y1_2425\17637-WebApps\uninest_mykey_new.pem" ec2-user@3.145.189.113

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

```
# Run in ubuntu:
# 1 wsl & login

# 2 
docker-compose build
docker-compose build --no-cache # clean rebuild

# 3
docker-compose up -d

# 4
docker-compose down
docker-compose logs
```

### Test user id:
```
{
  "email": "user0@example.com",
  "username": "user0",
  "user_type": "tenant",
  "password": "User0000",
  "confirm_password": "User0000"
}
```

### Commands:
1. reset db
```
curl -X POST "http://3.145.189.113:8000/api/v1/admin/fetch-real-properties?property_count=0" \
  -H "X-Admin-Key: Admin123456"
```
2. fetch
```
curl -X POST "http://3.145.189.113:8000/api/v1/admin/fetch-real-properties?property_count=5" \
  -H "X-Admin-Key: Admin123456"
```
3. Rebuild
```
sudo docker compose down && sudo docker compose up -d --build
```

### Bug list:
1. [/] `http://3.145.189.113/recommendation` This page didn't load Google Maps correctly. See the JavaScript console for technical details.
2. `http://3.145.189.113/preference` 
  Overall: the AI call respond is slow, sue
  The Image part
  - [/] doesn't have a loading icon when parsing the image
  The chat part
  - [/] doesn't have a initial message in the chat box "Let's talk about what kind of room you like!"
  - final reply message not showing the preference collected "Sure, it sounds like having a separate and spacious study room is an important factor for you in your new home. Here's the preference you provided: ```json ```"
3. `http://3.145.189.113/property-detail/46`:
 - landlord information not showing: image, original housing link, description details etc.
4. [/] Connect database to realworld data by 3rd party API

---
## Complete 3rd Party Real Estate API Integration

✅ 1. Multi-Source API Integration

Primary APIs Integrated:
- Realtor16 API - Main source for Pittsburgh properties
- Realty Mole API - Secondary rental listings
- Custom Pittsburgh Data - Neighborhood-specific properties near CMU

✅ 2. Advanced Multi-Source Fetcher (multi_source_fetcher.py)

Features:
- Smart Source Prioritization - Uses best APIs first
- Rate Limiting - Respects API limits
- Comprehensive Data Processing - Extracts detailed property info
- Automatic Landlord Creation - Creates verified landlord profiles
- Neighborhood Targeting - Focuses on CMU-area locations
- Error Handling - Graceful failures and retries

✅ 3. Enhanced Admin Endpoints

New Endpoints Added:

# Multi-source comprehensive sync
curl -X POST "http://3.145.189.113:8000/api/v1/admin/fetch-multi-source-properties?property_count=50" \
  -H "X-Admin-Key: Admin123456"

# Property source analytics
curl -X GET "http://3.145.189.113:8000/api/v1/admin/property-sources" \
  -H "X-Admin-Key: Admin123456"

✅ 4. Automated Sync Scheduler (sync_scheduler.py)

Automatic Scheduling:
- Daily Comprehensive Sync (6 AM) - Full data refresh
- Hourly Incremental Updates - Latest properties
- Weekly Cleanup (Sundays 3 AM) - Remove old listings

Scheduler Control Endpoints:

# Start automatic sync
curl -X POST "http://3.145.189.113:8000/api/v1/admin/sync/start" \
  -H "X-Admin-Key: Admin123456"

# Manual trigger any sync type
curl -X POST
"http://3.145.189.113:8000/api/v1/admin/sync/manual?sync_type=comprehensive" \
  -H "X-Admin-Key: Admin123456"

# Check scheduler status
curl -X GET "http://3.145.189.113:8000/api/v1/admin/sync/status" \
  -H "X-Admin-Key: Admin123456"

✅ 5. Real Estate Data Quality Features

Smart Data Processing:
- Address Normalization - Consistent formatting
- Price Validation - Realistic CMU-area pricing
- Coordinate Mapping - Accurate Pittsburgh locations
- Property Type Classification - Apartment, house, condo, etc.
- Duplicate Prevention - No duplicate listings
- Source Attribution - Track data origins

Pittsburgh Neighborhood Focus:
- Oakland, Shadyside, Squirrel Hill
- Greenfield, Point Breeze, Regent Square
- Bloomfield, Friendship
- All near CMU and University of Pittsburgh

✅ 6. Advanced Property Analytics

Data Quality Metrics:
- Properties by API source
- Neighborhood distribution
- Price range analysis
- Property type breakdown
- Coordinate coverage stats
- Update frequency tracking

🚀 How to Use

1. Quick Start - Fetch Real Properties Now:

curl -X POST "http://3.145.189.113:8000/api/v1/admin/fetch-multi-source-properties?property_count=100" \
  -H "X-Admin-Key: Admin123456"

2. Start Automatic Daily Sync:

curl -X POST "http://3.145.189.113:8000/api/v1/admin/sync/start" \
  -H "X-Admin-Key: Admin123456"

3. Check Your Data:

curl -X GET "http://3.145.189.113:8000/api/v1/admin/property-sources" \
  -H "X-Admin-Key: Admin123456"

📊 What You Get

- Real Properties from Realtor.com and other major sources
- Verified Landlords with contact information
- Accurate Coordinates for map display
- Pittsburgh Focus - CMU student-relevant areas
- Fresh Data - Automatic daily updates
- Source Attribution - Know where each property came from
- Quality Analytics - Monitor your data health