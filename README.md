# UniNest

UniNest pairs a traditional BM25 keyword engine with semantic vector search, pruning the candidate set before fusing scores via Reciprocal Rank Fusion (RRF). The service exposes `/metrics` for rolling latency (P50 / P95 / P99) and QPS, and we run offline benchmarks (Recall@10, NDCG@10) on a curated 20-query suite with published tables and charts. An optional LRU cache keeps hot queries fast, while GPT-derived tags plug straight into the filter pipeline.

- Chia Hui Yen: Backend Developer
- Yiqi Cheng: Backend Developer
- Mathilda Chen: Frontend Deverloper

- Demo link: http://3.145.189.113/

## Intention
UniNest is a full-stack web application designed to help students find housing recommendations near CMU. The platform features AI-powered chat assistance, intelligent image analysis for housing preferences, and roommate matching functionality.

## Technical Implementation Framework
- **Backend**: FastAPI (Python) + PostgreSQL
- **Frontend**: React + Vite + Tailwind CSS
- **AI Integration**: OpenAI GPT-4 (chat) + Vision API (image analysis)
- **Infrastructure**: Docker + AWS (EC2, RDS, S3)
- **Development**: Docker Compose for local orchestration

## Feature Screenshots
### User Register and Login
![User Register Feature](demo-recording/register.gif)

### AI Image Analysis and Chat Assistant for Preferences
![Chat Feature](demo-recording/ai-preference.gif)
![User Preference Result](demo-recording/user-preference.gif)

### Property Recommendations
![Recommendations](demo-recording/recommendation.gif)

### Potential Roommate Message
![Roommate Matching](demo-recording/message.gif)

### Landlord Register
![Landlord Register](demo-recording/landlord-register.gif)

### Landlord log properties
![Log Properties](demo-recording/log-properties.gif)
---

*Built to simplify the housing search process through intelligent recommendations and AI assistance.*
