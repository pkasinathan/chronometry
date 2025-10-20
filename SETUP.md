# Chronometry Setup Guide

Complete setup and configuration guide for Chronometry.

---

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Service Configuration](#service-configuration)
3. [Keyboard Shortcut Setup](#keyboard-shortcut-setup)
4. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Prerequisites

- macOS 10.14 or later
- Python 3.8+
- Access to Netflix Metatron and Copilot APIs

### Installation Steps

#### 1. Clone Repository
```bash
cd ~/workspace
git clone https://git.netflix.net/pkasinathan/chronometry.git
cd chronometry
```

#### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Verify Metatron CLI
```bash
which metatron  # Should return /usr/local/bin/metatron
```

#### 5. Configure
```bash
# Review and customize config if needed
cat config/config.yaml

# Key settings:
# - capture.fps: 0.00333333 (every 5 minutes)
# - annotation.batch_size: 3 (wait for 3 frames)
# - digest.interval_seconds: 3600 (every hour)
```

#### 6. Test Installation
```bash
python validate_system.py
```

Expected output: `✅ ALL TESTS PASSED!`

---

## Service Configuration

### Option A: Manual Start (Recommended for Testing)

**Start Agent** (capture + annotation + timeline + digest):
```bash
./bin/start_chronometry_agent.sh
```

**Start Web Dashboard** (separate terminal):
```bash
./bin/start_chronometry_webserver.sh
```

**Start Menu Bar App** (alternative to agent):
```bash
./bin/start_chronometry_menubar.sh
```

### Option B: Service Management (For Daily Use)

**Using the Service Manager:**
```bash
# Start all services
./bin/manage_services.sh start

# Stop all services
./bin/manage_services.sh stop

# Restart all services
./bin/manage_services.sh restart

# Check status
./bin/manage_services.sh status

# Individual services
./bin/manage_services.sh start menubar
./bin/manage_services.sh stop webserver
```

### Option C: macOS Launch Agents (Auto-start on Login)

**Install Services:**
```bash
# Copy plist files to LaunchAgents
cp config/com.chronometry.menubar.plist ~/Library/LaunchAgents/
cp config/com.chronometry.webserver.plist ~/Library/LaunchAgents/

# Update WorkingDirectory paths in plist files
# Change to your actual path:
sed -i '' "s|/Users/YOUR_USERNAME|$HOME|g" ~/Library/LaunchAgents/com.chronometry.*.plist

# Load services
launchctl load ~/Library/LaunchAgents/com.chronometry.menubar.plist
launchctl load ~/Library/LaunchAgents/com.chronometry.webserver.plist

# Start services
launchctl start com.chronometry.menubar
launchctl start com.chronometry.webserver
```

**Uninstall Services:**
```bash
# Stop services
launchctl stop com.chronometry.menubar
launchctl stop com.chronometry.webserver

# Unload services
launchctl unload ~/Library/LaunchAgents/com.chronometry.menubar.plist
launchctl unload ~/Library/LaunchAgents/com.chronometry.webserver.plist

# Remove plist files
rm ~/Library/LaunchAgents/com.chronometry.*.plist
```

**Check Service Status:**
```bash
# List loaded services
launchctl list | grep chronometry

# View logs
tail -f ~/Library/Logs/Chronometry/menubar.log
tail -f ~/Library/Logs/Chronometry/webserver.log
```

---

## Keyboard Shortcut Setup

### Enable Cmd+Shift+6 for "Capture Now"

The global keyboard shortcut allows you to capture screenshots instantly from any application.

#### Step 1: Grant Accessibility Permission

**macOS Ventura (13.0) and later:**
```
1. Open System Settings
2. Go to Privacy & Security → Accessibility
3. Click the lock icon 🔒 and authenticate
4. Click the + button
5. Navigate to /System/Applications/Utilities/
6. Select Terminal.app (or iTerm.app if you use that)
7. Ensure the checkbox is checked ✅
8. Click the lock icon 🔓
```

**macOS Monterey (12.0) and earlier:**
```
1. Open System Preferences
2. Go to Security & Privacy → Privacy tab
3. Select Accessibility from the left
4. Click the lock icon 🔒 and authenticate
5. Click the + button
6. Add Terminal.app or your shell application
7. Ensure checkbox is checked ✅
8. Click the lock icon 🔓
```

#### Step 2: Verify pynput Installation

```bash
cd /Users/pkasinathan/workspace/chronometry
source venv/bin/activate
python -c "import pynput; print('✅ pynput version:', pynput.__version__)"
```

Expected output: `✅ pynput version: 1.8.1`

#### Step 3: Restart Menubar App

```bash
# Stop if running
./bin/stop_chronometry_menubar.sh

# Start fresh
./bin/start_chronometry_menubar.sh
```

**Look for this log message:**
```
INFO - Global hotkey registered: Cmd+Shift+6 for Capture Now
```

#### Step 4: Test the Hotkey

1. **Press Cmd+Shift+6**
2. You should see notification: "✅ Screenshot saved: 20251009_HHMMSS.png"
3. Verify file created:
   ```bash
   ls -ltr data/frames/$(date +%Y-%m-%d)/ | tail -1
   ```

### Alternative Hotkey Combinations

If Cmd+Shift+6 conflicts with another app, you can change it:

**Edit**: `src/menubar_app.py` (around line 523)

```python
# Current
keyboard.HotKey.parse('<cmd>+<shift>+6')

# Alternatives:
keyboard.HotKey.parse('<cmd>+<shift>+7')    # Cmd+Shift+7
keyboard.HotKey.parse('<cmd>+<shift>+c')    # Cmd+Shift+C
keyboard.HotKey.parse('<cmd>+<alt>+6')      # Cmd+Option+6
keyboard.HotKey.parse('<ctrl>+<shift>+6')   # Ctrl+Shift+6
```

After changing, restart the menubar app.

---

## Troubleshooting

### Common Issues

#### Issue: Hotkey Doesn't Work

**Solution 1: Check Accessibility Permission**
```bash
# List apps with accessibility permission
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client FROM access WHERE service='kTCCServiceAccessibility'" 2>/dev/null
```

If Terminal isn't listed, grant permission (see Step 1 above).

**Solution 2: Check for Conflicts**
- Go to System Settings → Keyboard → Keyboard Shortcuts
- Check if another app uses Cmd+Shift+6
- If so, disable that shortcut or change Chronometry's hotkey

**Solution 3: Restart Everything**
```bash
./bin/stop_chronometry_menubar.sh
killall Terminal  # Or your shell app
# Reopen Terminal
./bin/start_chronometry_menubar.sh
```

#### Issue: No Notifications Appear

**Enable Notifications:**
```
System Settings → Notifications → Python (or Terminal)
- Allow Notifications: ON
- Banner Style: Alerts or Banners
```

#### Issue: "Port 8051 already in use"

```bash
# Find process using port 8051
lsof -i :8051

# Kill it
kill -9 $(lsof -t -i :8051)

# Restart web server
./bin/start_chronometry_webserver.sh
```

#### Issue: Virtual Environment Not Found

```bash
# Recreate venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue: Metatron Not Found

```bash
# Check metatron installation
which metatron

# If not found, install following Netflix documentation
# Usually at: /usr/local/bin/metatron
```

#### Issue: Annotations Not Running

**Check 1: Verify batch_size**
```bash
grep batch_size config/config.yaml
# Should show: batch_size: 3
```

**Check 2: Count frames**
```bash
# Need at least 3 unannotated frames
ls data/frames/$(date +%Y-%m-%d)/*.png | wc -l
```

**Check 3: Run manually**
```bash
source venv/bin/activate
export PYTHONPATH="$PWD/src"
python src/annotate.py
```

#### Issue: Digest Not Generating

**Check if enabled:**
```bash
grep -A 2 "digest:" config/config.yaml
```

**Generate manually:**
```bash
source venv/bin/activate
export PYTHONPATH="$PWD/src"
python src/digest.py
```

#### Issue: Web Dashboard Not Loading

**Check web server is running:**
```bash
ps aux | grep web_server.py
```

**Check logs:**
```bash
tail -50 logs/webserver.error.log
```

**Restart:**
```bash
./bin/stop_chronometry_webserver.sh
./bin/start_chronometry_webserver.sh
```

---

## Configuration Options

### Capture Frequency

**Edit**: `config/config.yaml`

```yaml
capture:
  fps: 0.00333333  # Every 5 minutes (1/300)
  
# Other options:
# fps: 0.00555556  # Every 3 minutes (1/180)
# fps: 0.00166667  # Every 10 minutes (1/600)
# fps: 0.01666667  # Every 1 minute (1/60)
```

### Annotation Batch Size

```yaml
annotation:
  batch_size: 3  # Wait for 3 frames before annotating
  
# Options:
# batch_size: 1  # Annotate every frame (more API calls)
# batch_size: 5  # Wait for 5 frames (fewer API calls)
```

### Digest Interval

```yaml
digest:
  enabled: true
  interval_seconds: 3600  # Every hour
  
# Options:
# interval_seconds: 1800  # Every 30 minutes
# interval_seconds: 7200  # Every 2 hours
```

### Data Retention

```yaml
capture:
  retention_days: 1095  # Keep data for 3 years
  
# Options:
# retention_days: 7    # Keep 1 week
# retention_days: 30   # Keep 1 month
# retention_days: 365  # Keep 1 year
```

---

## Advanced Setup

### Monitor Selection

To capture a specific monitor:

```yaml
capture:
  monitor_index: 1  # Primary monitor
  
# Options:
# monitor_index: 0  # All monitors
# monitor_index: 2  # Secondary monitor
```

**Find monitor index:**
```bash
python -c "import mss; sct = mss.mss(); print([f'{i}: {m}' for i, m in enumerate(sct.monitors)])"
```

### Custom Region Capture

To capture only a specific region:

```yaml
capture:
  region: [0, 0, 1920, 1080]  # [x, y, width, height]
  
# Example: Top-left quarter of 1920x1080 screen
# region: [0, 0, 960, 540]
```

---

## Verification

### Check Everything is Working

```bash
cd /Users/pkasinathan/workspace/chronometry

# 1. Test imports
source venv/bin/activate
python validate_system.py

# 2. Check services
./bin/manage_services.sh status

# 3. Test capture
python -c "
import sys; sys.path.insert(0, 'src')
from capture import capture_single_frame
from common import load_config
capture_single_frame(load_config(), False)
"

# 4. Test hotkey (after permission granted)
# Press Cmd+Shift+6

# 5. Open dashboard
open http://localhost:8051
```

---

## Daily Usage

### Starting Fresh Each Day

```bash
# Start services
./bin/manage_services.sh start

# Open dashboard
open http://localhost:8051

# Menu bar shows ⏱️ icon
# Click to Start Capture
```

### Using Capture Now

**When to use Cmd+Shift+6:**
- Important Slack conversation → Cmd+Shift+6
- Error message appears → Cmd+Shift+6
- Design review screen → Cmd+Shift+6
- Demo preparation → Cmd+Shift+6

### End of Day

```bash
# View your digest
open http://localhost:8051

# Stop services
./bin/manage_services.sh stop

# Or leave running for continuous monitoring
```

---

## Permissions Summary

Chronometry needs these macOS permissions:

| Permission | Required For | How to Grant |
|------------|--------------|--------------|
| **Screen Recording** | Screenshot capture | Grant when prompted on first run |
| **Accessibility** | Global hotkey (Cmd+Shift+6) | System Settings → Privacy → Accessibility |
| **Notifications** | Status updates | System Settings → Notifications → Python/Terminal |

---

## Next Steps

Once setup is complete:

1. ✅ **Start the agent**: `./bin/start_chronometry_agent.sh`
2. ✅ **Start web server**: `./bin/start_chronometry_webserver.sh`
3. ✅ **Open dashboard**: http://localhost:8051
4. ✅ **Test hotkey**: Press Cmd+Shift+6
5. ✅ **Let it run**: Captures will accumulate
6. ✅ **View digest**: After an hour, check dashboard

---

## Quick Reference

### Essential Commands

```bash
# Start everything
./bin/manage_services.sh start

# Stop everything
./bin/manage_services.sh stop

# Restart everything
./bin/manage_services.sh restart

# Check status
./bin/manage_services.sh status

# View logs
tail -f logs/menubar.log
tail -f logs/webserver.log

# Manual capture
Press Cmd+Shift+6

# Open dashboard
open http://localhost:8051
```

### File Locations

```
📁 Configuration:      config/config.yaml
📁 Screenshots:        data/frames/YYYY-MM-DD/*.png
📁 Annotations:        data/frames/YYYY-MM-DD/*.json
📁 Digests:           data/digests/digest_YYYY-MM-DD.json
📁 Token Usage:       data/token_usage/YYYY-MM-DD.json
📁 Timelines:         output/timeline_YYYY-MM-DD.html
📁 Logs:              logs/*.log
```

---

## Configuration via Web UI

You can also configure Chronometry through the web dashboard:

1. Open http://localhost:8051
2. Click **Settings** tab
3. Modify settings:
   - Capture FPS
   - Monitor index
   - Batch size
   - Digest interval
4. Click **Save Settings**

Changes are saved to `config/config.yaml` automatically.

---

## System Requirements

### Minimum

- macOS 10.14+
- Python 3.8+
- 2 GB RAM
- 1 GB free disk space

### Recommended

- macOS 12.0+
- Python 3.10+
- 4 GB RAM
- 5 GB free disk space (for longer retention)

### Network

- Access to Netflix Copilot API (copilotdpjava)
- Access to Netflix Metatron API (aiopsproxy)

---

## Support

**Documentation:**
- Main README: `README.md`
- Scripts Guide: `SCRIPTS.md`
- This Setup Guide: `SETUP.md`

**Logs:**
- Menu Bar: `logs/menubar.log`, `logs/menubar.error.log`
- Web Server: `logs/webserver.log`, `logs/webserver.error.log`

**Validation:**
```bash
python validate_system.py
```

---

**Setup Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: Complete  

🎉 **You're all set! Happy tracking!**

