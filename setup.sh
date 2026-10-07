#!/bin/bash
# setup_fixed.sh - Fixed installation script

echo "🚀 Kenya Election Tracker - Installation Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python3.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed. Installing pip...${NC}"
    sudo apt update
    sudo apt install python3-pip -y
fi

# Install python3-venv if not available
echo -e "${YELLOW}📦 Checking python3-venv...${NC}"
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}Installing python3-venv...${NC}"
    sudo apt update
    sudo apt install python3-venv python3-full -y
fi

# Check if Docker is available
DOCKER_AVAILABLE=false
if command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
    echo -e "${GREEN}✅ Docker detected${NC}"
else
    echo -e "${YELLOW}⚠️ Docker not detected. Using local database.${NC}"
fi

echo -e "${YELLOW}📦 Installing Backend Dependencies...${NC}"
cd backend

# Create virtual environment with proper Python version
python3 -m venv venv --without-pip
source venv/bin/activate

# Install pip in virtual environment
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py

# Upgrade pip
python3 -m pip install --upgrade pip

# Install requirements
python3 -m pip install -r requirements.txt

cd ..

echo -e "${YELLOW}📦 Installing Frontend Dependencies...${NC}"
cd frontend
npm install
cd ..

echo -e "${YELLOW}📦 Setting up environment files...${NC}"
# Create .env files if they don't exist
if [ ! -f backend/.env ]; then
    cat > backend/.env << EOF
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
DB_NAME=election_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
    echo -e "${GREEN}✅ Created backend/.env${NC}"
fi

if [ ! -f frontend/.env ]; then
    cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_MAPBOX_TOKEN=pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjbGF4eHh4eHh4eHh4eHh4eHh4eHh4eHgifQ.example
EOF
    echo -e "${GREEN}✅ Created frontend/.env${NC}"
fi

echo -e "${YELLOW}🗄️ Setting up database...${NC}"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "${GREEN}🐳 Starting Docker containers...${NC}"
    docker-compose up -d postgres redis 2>/dev/null || docker compose up -d postgres redis
    sleep 5
fi

cd backend
echo -e "${YELLOW}🔄 Running migrations...${NC}"
python3 manage.py makemigrations 2>/dev/null || python manage.py makemigrations
python3 manage.py migrate 2>/dev/null || python manage.py migrate

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Update .env files with your actual API keys"
echo "2. Download Kenya GeoJSON data (see alternative instructions below)"
echo "3. Start backend: cd backend && python manage.py runserver"
echo "4. Start frontend: cd frontend && npm start"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000/api"
echo "   Admin Panel: http://localhost:8000/admin"
echo ""
echo "📥 To download GeoJSON data, use one of these methods:"
echo "   Method 1: Download from browser:"
echo "   https://raw.githubusercontent.com/your-repo/kenya-geojson/main/kenya_counties.geojson"
echo ""
echo "   Method 2: Use wget with --no-check-certificate:"
echo "   wget --no-check-certificate https://raw.githubusercontent.com/your-repo/kenya-geojson/main/kenya_counties.geojson"
echo ""
echo "   Method 3: Use curl:"
echo "   curl -k -L -O https://raw.githubusercontent.com/your-repo/kenya-geojson/main/kenya_counties.geojson"