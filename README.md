# UniNest
Team: Chia Hui Yen, Mathilda, Yiqi

**Project Highlight**: 



## 🏗️ Project Overview


## Recommendation logic:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────►│  Auth Service   │────►│  User Profile   │
│   & Request     │     │  Verification   │     │  Retrieval      │
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

---
## Personal notes:
```
# 1 wsl & login

# 2 
docker-compose build

# 3
docker-compose up

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