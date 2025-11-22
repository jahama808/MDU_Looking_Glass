#!/bin/bash

# MDU Performance Dashboard - Installation Script (Linux/Mac)
# This script sets up the entire application environment

set -e  # Exit on any error

echo "========================================"
echo "MDU Performance Dashboard - Installer"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux or Mac
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="Mac"
else
    echo -e "${RED}Error: Unsupported operating system${NC}"
    echo "This script is designed for Linux and Mac only."
    echo "For Windows, please use install.bat"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Check for Python 3
echo "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Check for Node.js
echo "Checking for Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 16 or higher and try again."
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Found Node.js $NODE_VERSION${NC}"

# Check for npm
echo "Checking for npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    echo "Please install npm and try again."
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ Found npm $NPM_VERSION${NC}"
echo ""

# Create Python virtual environment
echo "========================================"
echo "Setting up Python environment..."
echo "========================================"

if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing...${NC}"
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install flask flask-cors pandas > /dev/null 2>&1
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Install frontend dependencies
echo "========================================"
echo "Setting up Frontend environment..."
echo "========================================"

cd frontend

if [ -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules already exists. Removing...${NC}"
    rm -rf node_modules
fi

echo "Installing Node.js dependencies (this may take a few minutes)..."
npm install > /dev/null 2>&1
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd ..
echo ""

# Create output directory
echo "========================================"
echo "Creating directories..."
echo "========================================"

mkdir -p output
echo -e "${GREEN}✓ Output directory created${NC}"
echo ""

# Check for data files
echo "========================================"
echo "Checking for data files..."
echo "========================================"

WAN_FILE=$(find . -name "networks_outage*.csv" -type f 2>/dev/null | head -1)
EERO_FILE=$(find . -name "*Eero*Discovery*.csv" -o -name "*eero*discovery*.csv" -type f 2>/dev/null | head -1)

if [ -n "$WAN_FILE" ] && [ -n "$EERO_FILE" ]; then
    echo -e "${GREEN}✓ Found data files:${NC}"
    echo "  WAN Connectivity: $WAN_FILE"
    echo "  Eero Discovery: $EERO_FILE"
    echo ""

    read -p "Would you like to process these files and create the database now? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Processing data files..."
        python process_property_outages_db.py \
            --connectivity-file "$WAN_FILE" \
            --discovery-file "$EERO_FILE" \
            --database ./output/outages.db
        echo -e "${GREEN}✓ Database created successfully${NC}"
    else
        echo -e "${YELLOW}Skipping database creation. You can run it manually later.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Data files not found${NC}"
    echo "Please add your CSV files and run:"
    echo "  source venv/bin/activate"
    echo "  python process_property_outages_db.py --connectivity-file <file> --discovery-file <file>"
fi
echo ""

# Create start scripts
echo "========================================"
echo "Creating start scripts..."
echo "========================================"

cat > start-backend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python api_server.py
EOF
chmod +x start-backend.sh
echo -e "${GREEN}✓ Created start-backend.sh${NC}"

cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
chmod +x start-frontend.sh
echo -e "${GREEN}✓ Created start-frontend.sh${NC}"

cat > start-all.sh << 'EOF'
#!/bin/bash

echo "Starting MDU Performance Dashboard..."
echo ""

# Start backend in background
echo "Starting API server on port 5000..."
source venv/bin/activate
python api_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo "Starting frontend dev server on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "========================================"
echo "MDU Performance Dashboard is running!"
echo "========================================"
echo ""
echo "Frontend: http://localhost:5173"
echo "API:      http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
EOF
chmod +x start-all.sh
echo -e "${GREEN}✓ Created start-all.sh${NC}"

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo -e "${GREEN}✓ Everything is set up and ready to go!${NC}"
echo ""
echo "To start the application:"
echo "  ./start-all.sh          - Start both backend and frontend"
echo "  ./start-backend.sh      - Start only the API server"
echo "  ./start-frontend.sh     - Start only the frontend"
echo ""
echo "To process data:"
echo "  source venv/bin/activate"
echo "  python process_property_outages_db.py --connectivity-file <file> --discovery-file <file>"
echo ""
echo "Access the application at: http://localhost:5173"
echo ""
