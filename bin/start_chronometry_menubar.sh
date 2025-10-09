#!/bin/bash

################################################################################
# Chronometry Menu Bar Application Launcher
################################################################################
#
# PURPOSE:
#   Starts the macOS menu bar application that provides quick access to
#   Chronometry controls and status from the system menu bar.
#
# WHAT IT DOES:
#   1. Validates environment (venv, rumps package, config)
#   2. Installs rumps library if not present (macOS menu bar framework)
#   3. Launches menubar_app.py which creates menu bar icon
#   4. Provides quick access to start/stop capture and view status
#
# MENU BAR FEATURES:
#   ⏱️  Menu Bar Icon          - Quick status indicator
#   📊 View Dashboard          - Opens web interface
#   ▶️  Start/Stop Capture     - Control data collection
#   📝 View Latest Annotations - Quick preview
#   ⚙️  Settings               - Quick configuration
#   ❌ Quit                    - Exit application
#
# USAGE:
#   ./start_chronometry_menubar.sh
#
# TO STOP:
#   Click menu bar icon → Quit
#   Or press Ctrl+C in terminal
#
# PLATFORM:
#   macOS only (requires rumps library and macOS API)
#
# REQUIREMENTS:
#   - macOS 10.14 or later
#   - Python 3.x with venv
#   - rumps >= 0.4.0 (auto-installed if missing)
#   - config.yaml in current directory
#
# GUI FEATURES:
#   - System tray integration
#   - Native macOS notifications
#   - Click-through to web dashboard
#   - Status indicators (running/stopped)
#
# TECHNICAL DETAILS:
#   - Uses Python rumps framework
#   - Runs in foreground (menu bar apps must)
#   - Communicates with web server API
#   - Can launch/stop other processes
#
# TROUBLESHOOTING:
#   - No menu bar icon: Check Console.app for Python errors
#   - Permission denied: Grant Terminal accessibility permissions
#   - rumps not found: Will auto-install on first run
#
# NOTES:
#   - Menu bar app must run in foreground
#   - Closing terminal will close menu bar app
#   - For persistent operation, use nohup or launch agent
#
# AUTHOR: Chronometry Team
# UPDATED: 2025-10-07
################################################################################

set -e

echo "Starting Chronometry Menu Bar App..."

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Error: Virtual environment not found at venv/bin/activate"
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install rumps if not already installed
if ! python -c "import rumps" 2>/dev/null; then
    echo "Installing rumps..."
    pip install rumps>=0.4.0
fi

# Verify config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "Error: config/config.yaml not found"
    echo "Please create a config/config.yaml file in the config directory."
    exit 1
fi

# Run the menu bar app
echo "Launching menu bar application..."
python src/menubar_app.py
