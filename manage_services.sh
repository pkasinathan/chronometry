#!/bin/bash

################################################################################
# Chronometry Service Manager
################################################################################
#
# PURPOSE:
#   Manage macOS launchd services for Chronometry web server and menu bar app.
#   Installs, starts, stops, and monitors both services automatically.
#
# FEATURES:
#   - Install services to run at boot
#   - Start/stop services on demand
#   - Check service status
#   - View service logs
#   - Uninstall services
#   - Auto-restart on crash
#
# USAGE:
#   ./manage_services.sh install   - Install services (run at boot)
#   ./manage_services.sh start     - Start services now
#   ./manage_services.sh stop      - Stop services
#   ./manage_services.sh restart   - Restart services
#   ./manage_services.sh status    - Check service status
#   ./manage_services.sh logs      - View service logs
#   ./manage_services.sh uninstall - Remove services
#
# SERVICES:
#   1. com.chronometry.webserver - Web dashboard (port 8051)
#   2. com.chronometry.menubar   - Menu bar application
#
# LOCATION:
#   Services installed to: ~/Library/LaunchAgents/
#
# LOGS:
#   Located in: ./logs/
#   - webserver.log / webserver.error.log
#   - menubar.log / menubar.error.log
#
# AUTHOR: Chronometry Team
# UPDATED: 2025-10-08
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
WEBSERVER_PLIST="com.chronometry.webserver.plist"
MENUBAR_PLIST="com.chronometry.menubar.plist"
LOGS_DIR="$SCRIPT_DIR/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check if a service is loaded
is_service_loaded() {
    local service_name=$1
    launchctl list | grep -q "$service_name"
}

# Function to install services
install_services() {
    echo ""
    echo "================================================"
    echo "  Installing Chronometry Services"
    echo "================================================"
    echo ""
    
    # Create LaunchAgents directory if it doesn't exist
    if [ ! -d "$LAUNCH_AGENTS_DIR" ]; then
        mkdir -p "$LAUNCH_AGENTS_DIR"
        print_info "Created $LAUNCH_AGENTS_DIR"
    fi
    
    # Copy plist files
    if [ -f "$SCRIPT_DIR/$WEBSERVER_PLIST" ]; then
        cp "$SCRIPT_DIR/$WEBSERVER_PLIST" "$LAUNCH_AGENTS_DIR/"
        print_success "Installed web server service"
    else
        print_error "Web server plist not found: $SCRIPT_DIR/$WEBSERVER_PLIST"
    fi
    
    if [ -f "$SCRIPT_DIR/$MENUBAR_PLIST" ]; then
        cp "$SCRIPT_DIR/$MENUBAR_PLIST" "$LAUNCH_AGENTS_DIR/"
        print_success "Installed menu bar service"
    else
        print_error "Menu bar plist not found: $SCRIPT_DIR/$MENUBAR_PLIST"
    fi
    
    # Load services
    echo ""
    print_info "Loading services..."
    launchctl load "$LAUNCH_AGENTS_DIR/$WEBSERVER_PLIST" 2>/dev/null || print_warning "Web server already loaded or failed to load"
    launchctl load "$LAUNCH_AGENTS_DIR/$MENUBAR_PLIST" 2>/dev/null || print_warning "Menu bar already loaded or failed to load"
    
    echo ""
    print_success "Services installed and started!"
    print_info "Services will start automatically on boot"
    print_info "Logs location: $LOGS_DIR"
    echo ""
}

# Function to start services
start_services() {
    echo ""
    echo "================================================"
    echo "  Starting Chronometry Services"
    echo "================================================"
    echo ""
    
    launchctl start com.chronometry.webserver
    print_success "Started web server"
    
    launchctl start com.chronometry.menubar
    print_success "Started menu bar app"
    
    echo ""
}

# Function to stop services
stop_services() {
    echo ""
    echo "================================================"
    echo "  Stopping Chronometry Services"
    echo "================================================"
    echo ""
    
    launchctl stop com.chronometry.webserver
    print_success "Stopped web server"
    
    launchctl stop com.chronometry.menubar
    print_success "Stopped menu bar app"
    
    echo ""
}

# Function to restart services
restart_services() {
    echo ""
    echo "================================================"
    echo "  Restarting Chronometry Services"
    echo "================================================"
    echo ""
    
    stop_services
    sleep 2
    start_services
}

# Function to check service status
check_status() {
    echo ""
    echo "================================================"
    echo "  Chronometry Services Status"
    echo "================================================"
    echo ""
    
    # Check web server
    if is_service_loaded "com.chronometry.webserver"; then
        print_success "Web Server: Running"
        launchctl list com.chronometry.webserver | grep -E "PID|LastExitStatus"
    else
        print_error "Web Server: Not running"
    fi
    
    echo ""
    
    # Check menu bar
    if is_service_loaded "com.chronometry.menubar"; then
        print_success "Menu Bar App: Running"
        launchctl list com.chronometry.menubar | grep -E "PID|LastExitStatus"
    else
        print_error "Menu Bar App: Not running"
    fi
    
    echo ""
    echo "Dashboard: http://localhost:8051"
    echo ""
}

# Function to view logs
view_logs() {
    echo ""
    echo "================================================"
    echo "  Viewing Chronometry Logs"
    echo "================================================"
    echo ""
    
    print_info "Press Ctrl+C to exit log view"
    echo ""
    
    # Tail both log files
    tail -f "$LOGS_DIR/webserver.log" "$LOGS_DIR/menubar.log" 2>/dev/null || {
        print_warning "Log files not found yet. Services may not have started."
        print_info "Log files will be created at:"
        echo "  - $LOGS_DIR/webserver.log"
        echo "  - $LOGS_DIR/menubar.log"
    }
}

# Function to uninstall services
uninstall_services() {
    echo ""
    echo "================================================"
    echo "  Uninstalling Chronometry Services"
    echo "================================================"
    echo ""
    
    # Unload services
    launchctl unload "$LAUNCH_AGENTS_DIR/$WEBSERVER_PLIST" 2>/dev/null || print_warning "Web server not loaded"
    launchctl unload "$LAUNCH_AGENTS_DIR/$MENUBAR_PLIST" 2>/dev/null || print_warning "Menu bar not loaded"
    
    # Remove plist files
    rm -f "$LAUNCH_AGENTS_DIR/$WEBSERVER_PLIST"
    rm -f "$LAUNCH_AGENTS_DIR/$MENUBAR_PLIST"
    
    print_success "Services uninstalled"
    print_info "Log files preserved in: $LOGS_DIR"
    echo ""
}

# Main command handler
case "${1:-}" in
    install)
        install_services
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    uninstall)
        uninstall_services
        ;;
    *)
        echo ""
        echo "Chronometry Service Manager"
        echo ""
        echo "Usage: $0 {install|start|stop|restart|status|logs|uninstall}"
        echo ""
        echo "Commands:"
        echo "  install   - Install services to run at boot"
        echo "  start     - Start services now"
        echo "  stop      - Stop services"
        echo "  restart   - Restart services"
        echo "  status    - Check service status"
        echo "  logs      - View service logs (live tail)"
        echo "  uninstall - Remove services completely"
        echo ""
        exit 1
        ;;
esac

exit 0

