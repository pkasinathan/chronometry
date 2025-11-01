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

# Change to project root directory (one level up from bin/)
cd "$(dirname "$0")/.."

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

# Verify config files exist (either split config or legacy)
if [ ! -f "config/user_config.yaml" ] || [ ! -f "config/system_config.yaml" ]; then
    if [ ! -f "config/config.yaml" ]; then
        echo "❌ Configuration files not found"
        echo "Please ensure either:"
        echo "  - config/user_config.yaml AND config/system_config.yaml exist (preferred)"
        echo "  - OR config/config.yaml exists (legacy)"
        exit 1
    fi
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

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"

# Start the web server
python src/web_server.py
