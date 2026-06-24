#!/bin/bash

# BuyAnywhere Deployment Script
# Run this script to deploy the application

set -e

echo "🚀 Starting BuyAnywhere Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p ssl
mkdir -p mongo-init

# Update environment variables for production
echo -e "${BLUE}🔧 Updating environment variables...${NC}"

# Backend environment
cat > backend/.env << EOF
MONGO_URL=mongodb://admin:buyanywhere2024@mongodb:27017/buyanywhere_prod?authSource=admin
DB_NAME=buyanywhere_prod
CORS_ORIGINS=https://rumarket.preview.emergentagent.com,http://localhost:3000
EMERGENT_LLM_KEY=sk-emergent-f5a879eA455CdD819C
EOF

# Frontend environment
cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=https://rumarket.preview.emergentagent.com/api
EOF

# Create MongoDB initialization script
cat > mongo-init/init.js << EOF
db = db.getSiblingDB('buyanywhere_prod');

// Create collections
db.createCollection('users');
db.createCollection('orders');
db.createCollection('user_sessions');

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.orders.createIndex({ "order_id": 1 }, { unique: true });
db.orders.createIndex({ "customer_info.email": 1 });
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 86400 });

print("Database initialized successfully");
EOF

# SSL Certificate generation (self-signed for development)
if [ ! -f "ssl/cert.pem" ]; then
    echo -e "${YELLOW}🔐 Generating self-signed SSL certificate...${NC}"
    echo -e "${YELLOW}⚠️  For production, replace with real SSL certificates${NC}"
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=BuyAnywhere/OU=IT Department/CN=shopanywhere-ru.preview.emergentagent.com"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.production.yml down || true

# Build and start containers
echo -e "${BLUE}🔨 Building and starting containers...${NC}"
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 30

# Create test users
echo -e "${BLUE}👤 Creating test users...${NC}"
docker-compose -f docker-compose.production.yml exec backend python create_test_user.py || echo "Users may already exist"

# Test the deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"

# Test backend health
if curl -f http://localhost:8001/health &> /dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

# Test frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend is not accessible${NC}"
fi

# Show status
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "\n${BLUE}📊 Service Status:${NC}"
docker-compose -f docker-compose.production.yml ps

echo -e "\n${BLUE}🔗 Access URLs:${NC}"
echo -e "Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "Backend API: ${GREEN}http://localhost:8001${NC}"
echo -e "API Docs: ${GREEN}http://localhost:8001/docs${NC}"

echo -e "\n${BLUE}🔑 Test Credentials:${NC}"
echo -e "Email: ${GREEN}test@buyanywhere.com${NC}"
echo -e "Password: ${GREEN}password123${NC}"
echo -e "\nOR"
echo -e "Email: ${GREEN}admin@buyanywhere.com${NC}"
echo -e "Password: ${GREEN}admin123${NC}"

echo -e "\n${YELLOW}📝 Next Steps:${NC}"
echo -e "1. Configure your domain DNS to point to this server"
echo -e "2. Replace self-signed SSL certificates with real ones"
echo -e "3. Update CORS_ORIGINS and REACT_APP_BACKEND_URL with your domain"
echo -e "4. Set up monitoring and backups"

echo -e "\n${BLUE}📋 Useful Commands:${NC}"
echo -e "View logs: ${GREEN}docker-compose -f docker-compose.production.yml logs -f${NC}"
echo -e "Stop services: ${GREEN}docker-compose -f docker-compose.production.yml down${NC}"
echo -e "Restart services: ${GREEN}docker-compose -f docker-compose.production.yml restart${NC}"

echo -e "\n${GREEN}✨ BuyAnywhere is now running!${NC}"