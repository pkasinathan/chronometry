# 🚀 Chronometry Service Setup Guide

## Quick Start: Run Chronometry at Boot

This guide shows you how to set up Chronometry to run automatically when your Mac starts, with automatic crash recovery.

---

## Prerequisites

1. **macOS** (10.14 or later)
2. **Python virtual environment** set up with dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **config.yaml** configured

---

## Installation (One-Time Setup)

### Step 1: Install Services

```bash
./manage_services.sh install
```

This will:
- ✅ Install web server and menu bar app as macOS services
- ✅ Start them immediately
- ✅ Configure them to start at login/boot
- ✅ Set up automatic restart on crash (10 second delay)
- ✅ Create log files in `./logs/`

### Step 2: Verify Services Are Running

```bash
./manage_services.sh status
```

Expected output:
```
================================================
  Chronometry Services Status
================================================

✓ Web Server: Running
PID = 12345
LastExitStatus = 0

✓ Menu Bar App: Running
PID = 12346
LastExitStatus = 0

Dashboard: http://localhost:8051
```

### Step 3: Check Menu Bar

Look for the ⏱️ icon in your macOS menu bar (top-right). Click it to access:
- Start/Stop Capture
- View Dashboard
- Generate Reports
- Settings

### Step 4: Access Dashboard

Open your browser to: **http://localhost:8051**

---

## Daily Usage

Once installed, services run automatically. No manual intervention needed!

### Menu Bar Access

Click the ⏱️ icon in your menu bar for quick controls.

### Web Dashboard

Always available at: **http://localhost:8051**

### View Logs

```bash
./manage_services.sh logs
```

Press `Ctrl+C` to exit log view.

---

## Service Management Commands

### Check Status

```bash
./manage_services.sh status
```

Shows if services are running, their PIDs, and last exit status.

### Restart Services

```bash
./manage_services.sh restart
```

Useful after configuration changes in `config.yaml`.

### Stop Services

```bash
./manage_services.sh stop
```

⚠️ Services will auto-restart after 10 seconds due to KeepAlive configuration.

### Uninstall Services

```bash
./manage_services.sh uninstall
```

Removes services from auto-start. They won't run at next boot.

---

## What Gets Auto-Started?

### 1. Web Server (`com.chronometry.webserver`)

- **Port**: 8051
- **Purpose**: Serves web dashboard and API
- **Logs**: `logs/webserver.log`, `logs/webserver.error.log`
- **Access**: http://localhost:8051

### 2. Menu Bar App (`com.chronometry.menubar`)

- **Purpose**: macOS menu bar controls
- **Logs**: `logs/menubar.log`, `logs/menubar.error.log`
- **Location**: ⏱️ icon in menu bar

---

## Auto-Restart Behavior

Both services are configured with `KeepAlive.Crashed = true`:

- If a service **crashes**, it will restart after **10 seconds**
- If a service **exits normally** (you stop it), it will restart after **10 seconds**
- **To truly stop**: Use `./manage_services.sh uninstall`

---

## File Locations

### Service Files

Located in: `~/Library/LaunchAgents/`

- `com.chronometry.webserver.plist`
- `com.chronometry.menubar.plist`

### Log Files

Located in: `./logs/` (in project directory)

- `webserver.log` - Web server output
- `webserver.error.log` - Web server errors
- `menubar.log` - Menu bar app output
- `menubar.error.log` - Menu bar app errors

### Configuration

- `config.yaml` - Main configuration file

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
tail -50 logs/webserver.error.log
tail -50 logs/menubar.error.log
```

**Check launchd status:**
```bash
launchctl list | grep chronometry
```

**Manual test:**
```bash
source venv/bin/activate
python web_server.py  # Should show any errors
```

### Port 8051 Already in Use

**Find and kill conflicting process:**
```bash
sudo lsof -i :8051
kill -9 <PID>
```

### Menu Bar Icon Not Appearing

**Check if process is running:**
```bash
ps aux | grep menubar_app.py
```

**Check permissions:**
- System Preferences → Security & Privacy → Privacy → Accessibility
- Ensure Terminal or your IDE has accessibility permissions

### Services Keep Crashing

**View crash logs:**
```bash
./manage_services.sh logs
```

**Check Python environment:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Verify config.yaml:**
```bash
cat config.yaml
```

---

## Advanced: Manual launchd Control

### Load Service

```bash
launchctl load ~/Library/LaunchAgents/com.chronometry.webserver.plist
```

### Unload Service

```bash
launchctl unload ~/Library/LaunchAgents/com.chronometry.webserver.plist
```

### List Services

```bash
launchctl list | grep chronometry
```

### View Service Details

```bash
launchctl list com.chronometry.webserver
```

### Start/Stop Service

```bash
launchctl start com.chronometry.webserver
launchctl stop com.chronometry.webserver
```

---

## Comparison: Manual vs Service Mode

| Feature | Manual (`./start_*.sh`) | Service Mode |
|---------|------------------------|--------------|
| **Starts at boot** | ❌ No | ✅ Yes |
| **Auto-restart on crash** | ❌ No | ✅ Yes |
| **Survives logout** | ❌ No | ✅ Yes |
| **Requires terminal** | ✅ Yes | ❌ No |
| **Log files** | Terminal output | `logs/*.log` |
| **Easy debugging** | ✅ Yes | ⚠️ Check logs |
| **Best for** | Development | Production |

---

## Uninstallation

To completely remove Chronometry services:

```bash
# Uninstall services
./manage_services.sh uninstall

# Verify removal
launchctl list | grep chronometry  # Should return nothing

# Optional: Remove log files
rm -rf logs/
```

---

## Tips

1. **Check logs regularly**: `./manage_services.sh logs`
2. **Restart after config changes**: `./manage_services.sh restart`
3. **Test manually first**: Use `./start_*.sh` scripts before installing services
4. **Monitor resource usage**: Activity Monitor → search "python"

---

## Summary

✅ **One-time setup**: `./manage_services.sh install`  
✅ **Always running**: Services start at boot  
✅ **Auto-recovery**: Services restart on crash  
✅ **Easy monitoring**: `./manage_services.sh status`  
✅ **Clean logs**: `./logs/*.log` files  

For more details, see [SCRIPTS.md](SCRIPTS.md).

