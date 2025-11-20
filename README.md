# ReelsAI

AI-powered video content management and recommendation system using RAG, Knowledge Graph, and Chatbot.

---

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Backend](#running-the-backend)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   Django API    │ (Port 8000)
│  - Video Save   │
│  - RAG Query    │
│  - Chatbot      │
│  - User Mgmt    │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ RabbitMQ │ (Port 5672)
    │  Queue   │
    └────┬─────┘
         │
    ┌────▼─────────┐
    │    Worker    │
    │ - Summarize  │
    │ - RAG Insert │
    │ - KG Build   │
    └──────────────┘

┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│  Supabase   │  │   Milvus     │  │    Neo4j     │
│  (Postgres) │  │  (Vector DB) │  │ (Graph DB)   │
└─────────────┘  └──────────────┘  └──────────────┘
```

---

## ✅ Prerequisites

### Required Software

- **Python** >= 3.11
- **PostgreSQL** (hoặc Supabase account)
- **Milvus** >= 2.3 (Vector Database)
- **Neo4j** >= 5.0 (Graph Database)
- **RabbitMQ** >= 3.12 (Message Queue)
- **Docker** (optional, for containerized services)

### External APIs

- **Google Gemini API Key** - For video summarization
- **Supabase Project** - For PostgreSQL database

---

## 📦 Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ReelsAI.git
cd ReelsAI
```

### 2. Create Virtual Environment

```bash
# Using conda (recommended)
conda create -n reelsai python=3.11
conda activate reelsai

# Or using venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install System Services

#### RabbitMQ

```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# macOS
brew install rabbitmq
brew services start rabbitmq

# Docker (alternative)
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

#### Milvus

```bash
# Docker Compose (recommended)
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.yml
docker-compose up -d

# Verify Milvus is running
curl http://localhost:19530/healthz
```

#### Neo4j

```bash
# Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5.0

# Or download from https://neo4j.com/download/
```

---

## ⚙️ Configuration

### 1. Environment Variables

Create `.env` file in project root:

```bash
# filepath: /home/aaronpham/Coding/ReelsAI/.env

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# RabbitMQ (default)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Django Settings

Update `backend/reelsai/settings.py` if needed (default values should work).

### 3. Initialize Databases

```bash
cd backend

# Django migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Setup Milvus Collection

```bash
# Run Milvus setup script
python -c "from apps.rag.milvus_setup import collection; print('Milvus ready')"
```

### 5. Setup Neo4j Schema (optional)

```bash
# Test Neo4j connection
python manage.py test_kg_pipeline
```

---

## 🚀 Running the Backend

### Start All Services

#### Terminal 1: Django API Server

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

**Available at:** http://localhost:8000

#### Terminal 2: Video Processing Worker

```bash
cd backend
python apps/saved_items/worker_video.py
```

**Logs:** Worker listens to RabbitMQ queue and processes video jobs

#### Terminal 3: RabbitMQ (if not using systemd)

```bash
rabbitmq-server
```

**Management UI:** http://localhost:15672 (guest/guest)

---

## 📚 API Documentation

### Swagger UI

Visit **http://localhost:8000/api/docs/** for interactive API documentation.

### Key Endpoints

#### 1. Save Video Item

```bash
POST /api/v1/save-item
Content-Type: application/json

{
  "user_id": 1,
  "content_id": 6952571625178975493
}
```

**Response:**

```json
{
  "status": "queued",
  "message": "Item saved. Video processing is queued.",
  "data": { ... }
}
```

#### 2. Query Saved Items (RAG)

```bash
POST /api/rag/query-items
Content-Type: application/json

{
  "user_id": "1",
  "query": "video về nấu ăn",
  "top_k": 5,
  "platform": "tiktok"
}
```

**Response:**

```json
{
  "query": "video về nấu ăn",
  "filter": "user_id == '1' && platform == 'tiktok'",
  "results": [
    {
      "content_id": "123",
      "summary": "Video hướng dẫn nấu phở...",
      "platform": "tiktok",
      "score": 0.95
    }
  ]
}
```

#### 3. Video Summarization

```bash
POST /api/video-analysis/summarize
Content-Type: application/json

{
  "video_url": "https://example.com/video.mp4"
}
```

**Or upload file:**

```bash
curl -X POST http://localhost:8000/api/video-analysis/summarize \
  -F "video_file=@/path/to/video.mp4"
```

#### 4. Add Item to RAG

```bash
PUT /api/rag/add-item
Content-Type: application/json

{
  "content_id": "123",
  "user_id": "1",
  "platform": "tiktok",
  "summary": "Video về du lịch Đà Nẵng..."
}
```

#### 5. Chatbot

```bash
POST /api/chatbot/chat
Content-Type: application/json

{
  "session_id": "user_123_session",
  "message": "Tìm video về nấu ăn cho tôi"
}
```

---

## 🧪 Testing

### Run Django Tests

```bash
cd backend
python manage.py test
```

### Test Individual Components

```bash
# Test video pipeline
python manage.py test_unified_pipeline

# Test KG construction
python manage.py test_kg_pipeline

# Test graph resolution
python manage.py test_graph_resolution

# Test chatbot
python manage.py test_chat_orchestrator
```

### Manual Testing

#### Test Save Item Flow

```bash
# 1. Save item
curl -X POST http://localhost:8000/api/v1/save-item \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "content_id": 1}'

# 2. Check worker logs (Terminal 2) for processing
# 3. Query saved items
curl -X POST http://localhost:8000/api/rag/query-items \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "test", "top_k": 5}'
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Milvus Connection Error

```bash
# Check Milvus status
docker ps | grep milvus
curl http://localhost:19530/healthz

# Restart Milvus
docker-compose restart
```

#### 2. RabbitMQ Connection Refused

```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# Restart
sudo systemctl restart rabbitmq-server

# View logs
sudo journalctl -u rabbitmq-server -f
```

#### 3. Gemini API 503 Overload

The system has automatic retry logic (3 attempts with exponential backoff). If still failing:

- Wait a few minutes and try again
- Check API quota: https://aistudio.google.com/app/apikey

#### 4. Neo4j Connection Error

```bash
# Check Neo4j
docker logs neo4j

# Access Neo4j Browser
open http://localhost:7474
# Login: neo4j / password123
```

#### 5. Worker Not Processing Jobs

```bash
# Check RabbitMQ queue
# Visit http://localhost:15672
# Login: guest/guest
# Check "Queues" tab for messages

# Restart worker
# Ctrl+C in Terminal 2, then:
python apps/saved_items/worker_video.py
```

#### 6. Django Migration Errors

```bash
# Reset migrations (careful in production!)
python manage.py migrate --fake apps/saved_items zero
python manage.py migrate apps/saved_items

# Or delete migration files and recreate
rm apps/saved_items/migrations/00*.py
python manage.py makemigrations saved_items
python manage.py migrate
```

---

## 📊 Monitoring

### Check System Health

```bash
# Django
curl http://localhost:8000/admin/  # Should return login page

# RabbitMQ
curl http://localhost:15672/api/overview  # Requires auth

# Milvus
curl http://localhost:19530/healthz

# Neo4j
curl http://localhost:7474/
```

### View Logs

```bash
# Django logs (in Terminal 1)
# Worker logs (in Terminal 2)

# RabbitMQ logs
sudo journalctl -u rabbitmq-server -f

# Milvus logs
docker logs -f milvus-standalone

# Neo4j logs
docker logs -f neo4j
```

---

## 📁 Project Structure

```
backend/
├── apps/
│   ├── saved_items/      # Video save & queue management
│   ├── rag/              # RAG service (Milvus)
│   ├── video_understanding/  # Video summarization
│   ├── chatbot/          # Conversational AI
│   ├── graph/            # Knowledge Graph (Neo4j)
│   └── users/            # User authentication
├── reelsai/              # Django project settings
├── manage.py
└── requirements.txt
```

---

## 🔧 Development Tips

### Hot Reload

Django auto-reloads when code changes. Worker needs manual restart.

### Debug Mode

Set `DEBUG=True` in `.env` for detailed error messages (don't use in production).

### Database Access

```bash
# Django shell
python manage.py shell

# Supabase web UI
open https://supabase.com/dashboard

# Neo4j Browser
open http://localhost:7474

# Milvus (use Attu UI)
docker run -p 8000:3000 -e MILVUS_URL=localhost:19530 zilliz/attu:latest
```

---

## 📝 Next Steps

1. ✅ Setup all services (PostgreSQL, Milvus, Neo4j, RabbitMQ)
2. ✅ Configure `.env` file
3. ✅ Run migrations
4. ✅ Start Django server
5. ✅ Start worker
6. ✅ Test via Swagger UI
7. 🚀 Build frontend integration

---

## 📞 Support

- **Issues:** https://github.com/yourusername/ReelsAI/issues
- **Email:** your-email@example.com

---

## 📄 License

MIT License - see LICENSE file for details
