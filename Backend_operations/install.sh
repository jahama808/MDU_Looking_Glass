#!/bin/bash

# Property Outage Analysis - Installation Script
# This script sets up a Python virtual environment and installs dependencies

set -e  # Exit on any error

echo "============================================================"
echo "Property Outage Analysis - Setup"
echo "============================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.6 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Found $PYTHON_VERSION"
echo ""

# Check if venv module is available
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Error: Python venv module is not available."
    echo "Please install python3-venv and try again."
    echo "  Ubuntu/Debian: sudo apt-get install python3-venv"
    echo "  Fedora/RHEL: sudo dnf install python3-venv"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old venv..."
    rm -rf venv
fi

python3 -m venv venv
echo "✓ Virtual environment created in ./venv"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "To use the script:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the script:"
echo "     python process_property_outages.py \\"
echo "       --connectivity-file wan_connectivity.csv \\"
echo "       --discovery-file eero_discovery.csv"
echo ""
echo "  3. When done, deactivate the virtual environment:"
echo "     deactivate"
echo ""
echo "For more information, see README.md"
echo ""
