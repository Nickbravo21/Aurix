#!/bin/bash
# Quick Start Script for Aurix

set -e

echo "🚀 Starting Aurix Platform..."
echo ""

# Add Poetry to PATH
export PATH="/home/nick-b/.local/bin:$PATH"

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "📦 Starting with Docker Compose..."
    cd "$(dirname "$0")"
    docker-compose -f infra/docker-compose.dev.yml up -d
    echo ""
    echo "✅ Aurix is starting up!"
    echo ""
    echo "Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/api/docs"
    echo "  - Frontend: http://localhost:3000"
    echo ""
    echo "View logs: docker-compose -f infra/docker-compose.dev.yml logs -f"
    echo "Stop: docker-compose -f infra/docker-compose.dev.yml down"
else
    echo "⚠️  Docker Compose not found. Starting services manually..."
    echo ""
    
    # Start PostgreSQL and Redis (if not running)
    echo "Starting PostgreSQL and Redis..."
    if ! pgrep -x "postgres" > /dev/null; then
        echo "Please start PostgreSQL manually: sudo systemctl start postgresql"
    fi
    
    if ! pgrep -x "redis-server" > /dev/null; then
        echo "Please start Redis manually: sudo systemctl start redis"
    fi
    
    # Start backend
    echo ""
    echo "Starting Backend API..."
    cd backend
    poetry run uvicorn src.main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Wait a bit for backend to start
    sleep 3
    
    # Start frontend
    echo "Starting Frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ Aurix is running!"
    echo ""
    echo "Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/api/docs"
    echo "  - Frontend: http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
fi
