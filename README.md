# Aurix — AI-Powered Financial Intelligence Platform

Aurix is an AI platform that automates financial analysis for businesses. It connects to tools like QuickBooks, Google Sheets, and Stripe to analyze cash flow, generate AI-powered insights, and provide real-time dashboards.

## 🚀 Features

- **Multi-source Integration**: Connect Google Sheets, QuickBooks, Stripe, and more
- **AI-Powered Analysis**: GPT-4o generates financial summaries, forecasts, and insights
- **Automated KPIs**: Revenue, expenses, burn rate, runway calculations
- **Time Series Forecasting**: Prophet-based predictions with confidence intervals
- **Smart Alerts**: Slack/email notifications for critical metrics
- **PDF Reports**: Automated report generation with AI summaries
- **Multi-tenant SaaS**: Secure, isolated data per organization

## 📋 Prerequisites

- **Backend**: Python 3.11+, Poetry
- **Frontend**: Node.js 20+, npm
- **Infrastructure**: Docker, Docker Compose, PostgreSQL, Redis
- **APIs**: OpenAI, Supabase, Google OAuth, QuickBooks, Stripe

## 🛠️ Tech Stack

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL + SQLModel (ORM)
- Celery + Redis (background tasks)
- Pandas + Prophet (analytics & forecasting)
- OpenAI GPT-4o (AI summaries)
- Integration: Google Sheets, QuickBooks, Stripe, Slack APIs

### Frontend
- Vite + React 18 + TypeScript
- TailwindCSS + shadcn/ui
- TanStack Query + Zustand
- React Router
- Recharts (visualizations)

## 📦 Installation

### Using Docker (Recommended)

```bash
# Clone repository
cd Aurix

# Copy environment files
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose -f infra/docker-compose.dev.yml up -d

# Check status
docker-compose -f infra/docker-compose.dev.yml ps
```

Services will be available at:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Frontend: http://localhost:3000

### Manual Setup

#### Backend

```bash
cd backend

# Install dependencies with Poetry
poetry install

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
poetry run alembic upgrade head

# Start API server
poetry run uvicorn src.main:app --reload

# Start Celery worker (in another terminal)
poetry run celery -A src.workers.celery_app worker --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🔑 Environment Configuration

### Required API Keys

1. **OpenAI**: Get from https://platform.openai.com/api-keys
2. **Supabase**: Create project at https://supabase.com
3. **Google OAuth**: https://console.cloud.google.com/apis/credentials
4. **QuickBooks**: https://developer.intuit.com
5. **Stripe**: https://dashboard.stripe.com/apikeys

### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 📊 Database Setup

```bash
# Create database
createdb aurix_db

# Run migrations
cd backend
poetry run alembic upgrade head

# Optional: Seed sample data
poetry run python scripts/seed_data.py
```

## 🧪 Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm test
```

## 🚢 Deployment

### Fly.io (Backend)

```bash
cd backend
fly launch
fly deploy
```

### Vercel (Frontend)

```bash
cd frontend
vercel --prod
```

### Environment Variables

Set these in your deployment platform:

**Backend**:
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `SUPABASE_*` (URL, keys)
- `GOOGLE_CLIENT_*`
- `QUICKBOOKS_CLIENT_*`
- `STRIPE_API_KEY`

**Frontend**:
- `VITE_API_URL` (backend URL)
- `VITE_SUPABASE_URL`

## 📖 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Key Endpoints

```
GET  /api/v1/analytics/kpis          # Get financial KPIs
GET  /api/v1/analytics/forecast/{metric}  # Get forecast
POST /api/v1/analytics/ai/summary    # Generate AI summary
POST /api/v1/datasources/connect     # Connect data source
GET  /api/v1/reports                 # List reports
```

## 🔒 Security

- JWT authentication via Supabase
- Encrypted OAuth tokens (Fernet)
- Row-level security (multi-tenant)
- Rate limiting on AI endpoints
- HTTPS in production
- Input sanitization

## 📈 Architecture

```
Frontend (React) → Backend API (FastAPI) → Database (PostgreSQL)
                        ↓
                   Celery Workers → Redis
                        ↓
              External APIs (OpenAI, Google, etc.)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Add tests for new features
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file

## 💬 Support

- Documentation: [docs.aurix.ai](https://docs.aurix.ai)
- Issues: GitHub Issues
- Discord: [discord.gg/aurix](https://discord.gg/aurix)

## 🗺️ Roadmap

- [ ] Plaid integration for bank accounts
- [ ] Custom report builder
- [ ] Mobile app
- [ ] Advanced ML models
- [ ] Multi-currency support
- [ ] API webhooks
- [ ] Team collaboration features

---

Built with ❤️ by the Aurix team
