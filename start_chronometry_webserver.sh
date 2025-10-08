#!/bin/bash

################################################################################
# Chronometry Web Server Launcher
################################################################################
#
# PURPOSE:
#   Starts the Chronometry web-based dashboard on port 8051, providing
#   real-time access to work activity data through a modern web interface.
#
# WHAT IT DOES:
#   1. Validates environment (venv, Flask, config)
#   2. Starts Flask web server on http://localhost:8051
#   3. Serves interactive dashboard with 5 main tabs
#   4. Provides REST API endpoints for data access
#   5. Enables WebSocket connections for real-time updates
#
# WEB INTERFACE FEATURES:
#   📊 Dashboard  - Overview stats and today's digest
#   📅 Timeline   - Detailed activity timeline view
#   📈 Analytics  - Charts and productivity insights
#   🔍 Search     - Search through activities
#   ⚙️  Settings  - Configure capture and digest settings
#
# API ENDPOINTS:
#   GET  /api/health               - Health check
#   GET  /api/stats                - Overall statistics
#   GET  /api/timeline             - Activity timeline
#   GET  /api/timeline/<date>      - Timeline for specific date
#   GET  /api/digest               - Today's AI digest
#   GET  /api/digest/<date>        - Digest for specific date
#   GET  /api/config               - Current configuration
#   PUT  /api/config               - Update configuration
#   GET  /api/search               - Search activities
#   GET  /api/analytics            - Analytics data
#   GET  /api/frames               - List of captured frames
#   GET  /api/dates                - Available dates
#
# USAGE:
#   ./start_chronometry_webserver.sh
#
# TO STOP:
#   Press Ctrl+C
#
# TO RUN IN BACKGROUND:
#   ./start_chronometry_webserver.sh > web_server.log 2>&1 &
#   # Save PID: echo $! > web_server.pid
#
# ACCESS:
#   Dashboard: http://localhost:8051
#   API:       http://localhost:8051/api
#   Health:    http://localhost:8051/api/health
#
# REQUIREMENTS:
#   - Python 3.x with venv
#   - Flask, flask-cors, flask-socketio, pandas
#   - config.yaml in current directory
#   - data/frames/ directory with captured data
#
# PORT:
#   8051 (configurable in web_server.py)
#
# LOG FILE:
#   Standard output (redirect to file if running in background)
#
# TROUBLESHOOTING:
#   - Port already in use: sudo lsof -i :8051
#   - Dependencies missing: pip install -r requirements.txt
#   - No data: Run start_chronometry_agent.sh first
#
# AUTHOR: Chronometry Team
# UPDATED: 2025-10-07
################################################################################

set -e  # Exit on error

echo "================================================"
echo "  Chronometry Web Server"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "❌ config.yaml not found!"
    echo "Please ensure config.yaml exists in the current directory"
    exit 1
fi

echo ""
echo "✅ Starting web server..."
echo ""
echo "🌐 Dashboard URL: http://localhost:8051"
echo "📊 API Endpoint: http://localhost:8051/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "================================================"
echo ""

# Start the web server
python web_server.py
