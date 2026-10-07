#!/bin/bash

echo "🚀 Kenya Election Tracker - Complete Backend Setup"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python3.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create migrations
echo -e "${YELLOW}🔄 Creating migrations...${NC}"
python manage.py makemigrations

# Apply migrations
echo -e "${YELLOW}🔄 Applying migrations...${NC}"
python manage.py migrate

# Seed data
echo -e "${YELLOW}📊 Seeding sample data...${NC}"
python seed_data.py

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 To start the server:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "🌐 Access the application:"
echo "   API: http://localhost:8000/api/"
echo "   Admin: http://localhost:8000/admin/"
echo ""
echo "👤 Default admin: admin / admin123"
