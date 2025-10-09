# Setting Up Cmd+Shift+6 Hotkey for Capture Now

## Quick Setup Guide

Follow these steps to enable the global keyboard shortcut **Cmd+Shift+6** for instant screenshot capture.

---

## Prerequisites

✅ Chronometry installed and working  
✅ pynput package installed (`pip install pynput`)  
✅ macOS 10.14 or later  

---

## Step-by-Step Setup

### Step 1: Install pynput (If Not Already Installed)

```bash
cd /Users/pkasinathan/workspace/chronometry
source venv/bin/activate
pip install pynput>=1.7.6
```

**Verify Installation:**
```bash
python -c "import pynput; print('✅ pynput installed:', pynput.__version__)"
```

---

### Step 2: Grant Accessibility Permission

This is **REQUIRED** for global hotkeys to work.

#### Option A: System Settings (macOS Ventura+)

1. Open **System Settings**
2. Click **Privacy & Security** in the sidebar
3. Click **Accessibility**
4. Click the **lock icon** 🔒 at the bottom and authenticate
5. Click the **+** button
6. Navigate to and select **Terminal.app** (or your shell application)
   - **Path**: `/System/Applications/Utilities/Terminal.app`
   - **Or if using iTerm**: `/Applications/iTerm.app`
   - **Or if using Cursor/VSCode Terminal**: Add those apps
7. Ensure the checkbox is **checked** ✅
8. Click the lock icon 🔓 to prevent further changes

#### Option B: System Preferences (macOS Monterey and earlier)

1. Open **System Preferences**
2. Click **Security & Privacy**
3. Click the **Privacy** tab
4. Select **Accessibility** from the left sidebar
5. Click the **lock icon** 🔒 to make changes
6. Click the **+** button
7. Add **Terminal.app** or your shell
8. Click the lock icon 🔓 when done

---

### Step 3: Start the Menubar App

```bash
cd /Users/pkasinathan/workspace/chronometry
./bin/start_chronometry_menubar.sh
```

**Look for this log message:**
```
INFO - Global hotkey registered: Cmd+Shift+6 for Capture Now
```

---

### Step 4: Test the Hotkey

**Test 1: Press the Hotkey**
```
1. Press: Cmd+Shift+6
2. You should see: Notification "📸 Capturing screenshot now..."
3. Then: Notification "✅ Screenshot saved: 20251009_HHMMSS.png"
```

**Test 2: Verify Screenshot**
```bash
ls -ltr data/frames/$(date +%Y-%m-%d)/ | tail -1
```

**Test 3: Check Statistics**
```
1. Click ⏱️ in menu bar
2. Click "Statistics"
3. Should show: "Manual Captures: 1"
```

---

## Verification Checklist

Use this checklist to ensure everything is set up correctly:

- [ ] pynput installed (`python -c "import pynput"`)
- [ ] Accessibility permission granted for Terminal/shell
- [ ] Menubar app starts without errors
- [ ] Log shows "Global hotkey registered"
- [ ] Pressing Cmd+Shift+6 shows notification
- [ ] Screenshot file appears in data/frames/<date>/
- [ ] Statistics shows manual capture count

---

## Troubleshooting

### Hotkey Doesn't Trigger

**Check 1: Accessibility Permission**
```bash
# Run this command - if it returns nothing, permission is missing
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client FROM access WHERE service='kTCCServiceAccessibility'" 2>/dev/null
```

**Fix**: Re-do Step 2 above

---

**Check 2: Conflicting Hotkey**
```
Some apps might already use Cmd+Shift+6
Try: System Settings → Keyboard → Keyboard Shortcuts
Check for conflicts
```

**Fix**: If conflicting, you can modify the hotkey in `menubar_app.py`:
```python
# Change from:
keyboard.HotKey.parse('<cmd>+<shift>+6')

# To another key, e.g.:
keyboard.HotKey.parse('<cmd>+<shift>+7')  # Cmd+Shift+7
keyboard.HotKey.parse('<cmd>+<shift>+c')  # Cmd+Shift+C
keyboard.HotKey.parse('<ctrl>+<shift>+6')  # Ctrl+Shift+6
```

---

**Check 3: pynput Not Running**
```bash
# Check if pynput is actually running
tail -20 logs/menubar.log
# Look for errors related to pynput or keyboard
```

**Fix**: Restart menubar app

---

### Permission Denied Error

**Error Message:**
```
Error: Unable to access key listeners
```

**Solution:**
```
1. System Settings → Privacy & Security
2. Add your shell app to BOTH:
   - Accessibility
   - Input Monitoring
3. Restart shell
4. Restart menubar app
```

---

### Hotkey Works But No Screenshot

**Possible Causes:**
1. Screen is locked → Expected behavior
2. Camera is active → Expected behavior (creates synthetic annotation)
3. Disk full → Check disk space
4. Permission error → Check data/ folder permissions

**Debugging:**
```bash
# Watch logs in real-time
tail -f logs/menubar.log

# Press Cmd+Shift+6 and watch for:
INFO - Hotkey Cmd+Shift+6 pressed - triggering capture
INFO - Captured: 20251009_HHMMSS.png
```

---

## Alternative: Menu Bar Click

If you don't want to use the hotkey or have permission issues:

**Just use the menu:**
```
1. Click ⏱️ in menu bar
2. Click "📸 Capture Now (⌘⇧6)"
3. Done! No special permissions needed
```

---

## Advanced Configuration

### Change Hotkey Combination

**Edit**: `src/menubar_app.py` line ~522

```python
# Current hotkey
keyboard.HotKey.parse('<cmd>+<shift>+6')

# Alternative options:
'<cmd>+<shift>+c'     # Cmd+Shift+C
'<cmd>+<shift>+s'     # Cmd+Shift+S
'<cmd>+<alt>+6'       # Cmd+Option+6
'<ctrl>+<shift>+6'    # Ctrl+Shift+6
'<cmd>+<shift>+space' # Cmd+Shift+Space
```

**After changing**, restart the menubar app:
```bash
./bin/stop_chronometry_menubar.sh
./bin/start_chronometry_menubar.sh
```

---

### Disable Hotkey (Menu Only)

If you want to use only the menu item without global hotkey:

**Edit**: `src/menubar_app.py`

```python
# Comment out this line in __init__:
# self.setup_hotkey()
```

Or just don't grant accessibility permission - the menu item will still work!

---

## Testing Script

Run this to test the feature:

```bash
cd /Users/pkasinathan/workspace/chronometry
source venv/bin/activate

# Test capture_single_frame function
python -c "
import sys
sys.path.insert(0, 'src')
from capture import capture_single_frame
from common import load_config

config = load_config()
print('Testing manual capture...')
success = capture_single_frame(config, show_notifications=False)
print(f'Result: {'✅ Success' if success else '❌ Failed/Skipped'}')
"
```

---

## Summary

**What You Get:**
- 📸 Instant screenshot capture via Cmd+Shift+6
- 📋 Menu bar option for manual capture
- 📊 Statistics tracking for manual vs automatic
- 🔒 Privacy-aware (respects locks and camera)

**Setup Time:** ~5 minutes (mainly granting permission)

**Once Setup:**
- ✅ Works globally across all apps
- ✅ Non-intrusive (background capture)
- ✅ Fast (<1 second execution)
- ✅ Reliable notification feedback

---

## Need Help?

**Check Logs:**
```bash
tail -50 logs/menubar.log
```

**Test Permissions:**
```bash
# This should work if permissions are correct
python -c "from pynput import keyboard; print('✅ pynput working')"
```

**Reset and Retry:**
```bash
./bin/stop_chronometry_menubar.sh
./bin/start_chronometry_menubar.sh
# Then test Cmd+Shift+6
```

---

**Status**: Ready to Use  
**Hotkey**: Cmd+Shift+6  
**Menu**: 📸 Capture Now  

🎉 **Happy Manual Capturing!**

