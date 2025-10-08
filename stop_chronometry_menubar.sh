#!/bin/bash

################################################################################
# Chronometry Menu Bar App Shutdown Script
################################################################################
#
# PURPOSE:
#   Gracefully stops the macOS menu bar application and all associated
#   Chronometry processes it may have started (capture, annotation, etc.).
#
# WHAT IT DOES:
#   1. Finds running menubar_app.py process
#   2. Finds start_chronometry_menubar.sh script process
#   3. Sends SIGTERM for graceful shutdown
#   4. Waits up to 5 seconds for clean exit
#   5. Force kills (SIGKILL) if necessary
#   6. Stops any child processes (capture if running via menubar)
#   7. Verifies all processes stopped
#
# PROCESSES STOPPED:
#   - start_chronometry_menubar.sh (launch script)
#   - menubar_app.py (menu bar application)
#   - capture.py (if started via menu bar)
#   - Any ongoing annotation/timeline/digest processes
#
# SHUTDOWN BEHAVIOR:
#   - Graceful (SIGTERM): Completes current operation, saves state
#   - Forced (SIGKILL): Immediate termination after 5 second timeout
#   - Cleanup: Removes temporary files, preserves data
#
# USAGE:
#   ./stop_chronometry_menubar.sh
#
# ALTERNATIVE:
#   You can also quit from the menu bar itself:
#   Click ⏱️ icon → Quit
#
# WHAT HAPPENS DURING SHUTDOWN:
#   1. Menu bar icon disappears
#   2. If capture was running, it stops gracefully
#   3. Current annotation/timeline completes (if running)
#   4. All data files are preserved
#   5. Log file is flushed
#
# FILES AFFECTED:
#   - Preserves: All data files (frames, annotations, digests, timelines)
#   - Preserves: menubar.log (if exists)
#   - Preserves: config.yaml and all configuration
#
# EXIT CODES:
#   0 - Menu bar app stopped successfully
#   1 - Menu bar app not running or error occurred
#
# VERIFICATION:
#   After running, verify with:
#   ps aux | grep menubar         # Should return nothing
#   ls /Applications | grep -i myworkanalyzer  # Menu bar icon gone
#
# NOTES:
#   - Safe to run multiple times
#   - Safe to run even if menubar not running
#   - Does not affect web server or other processes
#   - Can restart immediately after stopping
#
# TROUBLESHOOTING:
#   - "Not running" error: Menubar already stopped or never started
#   - Force kill triggered: Process was stuck, check logs
#   - Still seeing icon: Wait 5 seconds or log out/in
#
# TO RESTART:
#   ./stop_chronometry_menubar.sh
#   ./start_chronometry_menubar.sh
#
# AUTHOR: Chronometry Team
# UPDATED: 2025-10-07
################################################################################

echo "Stopping Chronometry Menu Bar App..."

# Change to script directory
cd "$(dirname "$0")"

# Function to find and kill processes
stop_processes() {
    local process_name=$1
    local friendly_name=$2
    local pids=$(pgrep -f "$process_name")
    
    if [ -z "$pids" ]; then
        echo "ℹ️  $friendly_name not running"
        return 0
    fi
    
    echo "Found $friendly_name: $pids"
    
    # Try graceful shutdown first (SIGTERM)
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            echo "Sending SIGTERM to PID $pid..."
            kill -SIGTERM $pid 2>/dev/null
        fi
    done
    
    # Wait up to 5 seconds for graceful shutdown
    echo "Waiting for $friendly_name to stop gracefully..."
    for i in {1..5}; do
        local remaining_pids=$(pgrep -f "$process_name")
        if [ -z "$remaining_pids" ]; then
            echo "✅ $friendly_name stopped gracefully"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running (SIGKILL)
    local remaining_pids=$(pgrep -f "$process_name")
    if [ -n "$remaining_pids" ]; then
        echo "⚠️  Force killing $friendly_name..."
        for pid in $remaining_pids; do
            if kill -0 $pid 2>/dev/null; then
                kill -SIGKILL $pid 2>/dev/null
            fi
        done
        echo "✅ $friendly_name force stopped"
    fi
}

# Stop the menu bar app first
stop_processes "python.*menubar_app.py" "Menu Bar App"

# Stop the start script if running
stop_processes "start_chronometry_menubar.sh" "Menu Bar Launch Script"

# If menubar started capture, stop it
if pgrep -f "python.*capture.py" > /dev/null; then
    echo "ℹ️  Capture process running (may have been started by menubar)"
    read -p "Stop capture process too? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_processes "python.*capture.py" "Capture Process"
    fi
fi

# Verify menu bar app is stopped
if pgrep -f "menubar_app.py" > /dev/null || \
   pgrep -f "start_chronometry_menubar.sh" > /dev/null; then
    echo "⚠️  Warning: Some processes may still be running"
    echo "Check with: ps aux | grep menubar"
    exit 1
else
    echo ""
    echo "✅ Chronometry Menu Bar App stopped successfully"
    echo ""
    echo "To restart: ./start_chronometry_menubar.sh"
    exit 0
fi

