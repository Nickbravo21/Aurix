# Aurix Project Setup Guide

## 🎯 Quick Start

### 1. Prerequisites Installation

Make sure you have the following installed:
- **Python 3.11+** and Poetry
- **Node.js 20+** and npm
- **Docker & Docker Compose**
- **PostgreSQL 16** (if not using Docker)
- **Redis 7** (if not using Docker)

### 2. Clone and Setup

```bash
cd /home/nick-b/Downloads/Aurix
```

### 3. Backend Setup

```bash
cd backend

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# IMPORTANT: Edit .env and add your API keys:
# - OPENAI_API_KEY
# - SUPABASE credentials
# - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
# - QUICKBOOKS_CLIENT_ID and QUICKBOOKS_CLIENT_SECRET
# - STRIPE_API_KEY
# - Generate ENCRYPTION_KEY with:
poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Start backend (if using Docker, skip to Docker section)
poetry run uvicorn src.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env and set:
# - VITE_API_URL=http://localhost:8000/api/v1
# - VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

# Start frontend
npm run dev
```

### 5. Using Docker (Recommended)

```bash
# From project root
docker-compose -f infra/docker-compose.dev.yml up -d

# Check logs
docker-compose -f infra/docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f infra/docker-compose.dev.yml down
```

## 🔑 Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Add to `.env` as `OPENAI_API_KEY=sk-...`

### Supabase
1. Create project at https://supabase.com
2. Go to Settings > API
3. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_JWT_PUBLIC_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`

### Google OAuth
1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Google Sheets API and Google Drive API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/api/v1/datasources/oauth/google/callback`
6. Copy Client ID and Client Secret

### QuickBooks
1. Create app at https://developer.intuit.com
2. Get Client ID and Client Secret
3. Add redirect URI: `http://localhost:8000/api/v1/datasources/oauth/quickbooks/callback`

### Stripe
1. Create account at https://dashboard.stripe.com
2. Go to Developers > API Keys
3. Copy Secret key
4. Optional: Create webhook endpoint for production

### Slack (Optional)
1. Create app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `channels:read`
3. Install app to workspace
4. Copy Bot User OAuth Token

## 📊 Database Setup

### Using Docker
Database is automatically created and initialized.

### Manual Setup
```bash
# Create database
createdb aurix_db

# Run migrations (when implemented)
cd backend
poetry run alembic upgrade head
```

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Example API Calls

```bash
# Get KPIs (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/kpis

# Generate AI Summary
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/ai/summary
```

## 🏗️ Project Structure

```
Aurix/
├── backend/
│   ├── src/
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # Database models & session
│   │   ├── integrations/   # External API clients
│   │   ├── etl/            # Data processing & KPIs
│   │   ├── ai/             # OpenAI integration
│   │   ├── api/            # FastAPI routes
│   │   ├── workers/        # Celery background tasks
│   │   └── main.py         # FastAPI application
│   ├── pyproject.toml      # Python dependencies
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── features/       # Feature modules
│   │   ├── components/     # Reusable components
│   │   ├── lib/            # Utilities
│   │   ├── store/          # State management
│   │   └── main.tsx        # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── infra/
│   ├── docker-compose.dev.yml
│   ├── fly.toml
│   └── nginx.conf
│
└── README.md
```

## 🔧 Development Workflow

### Running Tests
```bash
# Backend
cd backend
poetry run pytest

# Frontend
cd frontend
npm test
```

### Code Formatting
```bash
# Backend
cd backend
poetry run black src/
poetry run ruff check src/

# Frontend
cd frontend
npm run lint
```

### Database Migrations
```bash
cd backend

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Running Celery Worker
```bash
cd backend
poetry run celery -A src.workers.celery_app worker --loglevel=info
```

## 🚀 Deployment

### Backend (Fly.io)
```bash
cd backend
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set DATABASE_URL=postgresql://...
fly deploy
```

### Frontend (Vercel)
```bash
cd frontend
npm run build
vercel --prod
```

### Environment Variables for Production
Make sure to set all required environment variables in your deployment platform.

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Backend
cd backend
poetry install

# Frontend
cd frontend
npm install
```

### Database connection errors
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- Check database exists: `psql -l`

### Redis connection errors
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL in .env

### API Key errors
- Ensure all required API keys are set in .env
- Check keys are valid and not expired
- Verify correct environment (sandbox vs production)

## 📚 Next Steps

1. **Set up Supabase Authentication**
   - Create auth tables
   - Implement login/signup
   - Add JWT verification

2. **Implement Additional Routers**
   - `/api/v1/datasources` - Data source management
   - `/api/v1/reports` - Report generation
   - `/api/v1/alerts` - Alert rules
   - `/api/v1/billing` - Stripe billing

3. **Complete Frontend**
   - Connect to backend API
   - Implement authentication flow
   - Add charts and visualizations
   - Build data source connection UI

4. **Add Tests**
   - Unit tests for core logic
   - Integration tests for API
   - E2E tests for critical flows

5. **Performance Optimization**
   - Add caching (Redis)
   - Optimize database queries
   - Implement pagination
   - Add rate limiting

6. **Monitoring & Logging**
   - Set up error tracking (Sentry)
   - Add application monitoring
   - Configure log aggregation

## 🤝 Support

For questions or issues:
1. Check the documentation
2. Search existing issues
3. Create a new issue with details

---

**Built with optimized, production-ready architecture** ✨
