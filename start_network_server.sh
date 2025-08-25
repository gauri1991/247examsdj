#!/bin/bash

# Script to start Django development server accessible from local network
# Make sure to stop any existing Django processes first

echo "Starting Django server accessible from local network..."
echo "Your local IP: 192.168.29.81"
echo ""
echo "Server will be accessible at:"
echo "  - http://192.168.29.81:5000"
echo "  - http://dts.com:5000 (if hostname is configured)"
echo ""

# Check if virtual environment exists and is functional
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment 'venv' not found!"
    echo "Please create virtual environment first:"
    echo "  sudo apt install python3.12-venv"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "Error: Django not found in virtual environment!"
    echo "Please install requirements:"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Start Django development server bound to all interfaces
# Try python3 first, fallback to python
if command -v python3 >/dev/null 2>&1; then
    python3 manage.py runserver 0.0.0.0:5000
elif command -v python >/dev/null 2>&1; then
    python manage.py runserver 0.0.0.0:5000
else
    echo "Error: Neither python nor python3 command found!"
    exit 1
fi

echo ""
echo "To access from other devices on your network, use:"
echo "  - http://192.168.29.81:5000"
echo "  - http://dts.com:5000 (after configuring hosts file)"