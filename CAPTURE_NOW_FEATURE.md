# Capture Now Feature - Manual Ad-hoc Screenshots

## Date: October 9, 2025

## Overview

Added "Capture Now" feature for manual, ad-hoc screenshot capture in addition to the periodic automatic capture. This allows you to capture important moments on-demand via menu bar or global keyboard shortcut.

---

## Features Added

### 1. **Menu Bar Option**
- New menu item: **"📸 Capture Now (⌘⇧6)"**
- Located below "Pause" in the menu
- Works independently of automatic capture (can use even when capture is stopped)

### 2. **Global Keyboard Shortcut**
- **Cmd+Shift+6** triggers instant capture
- Works system-wide (no need to have menu open)
- Non-blocking - runs in background thread

### 3. **Smart Capture Logic**
- Respects screen lock status (won't capture if locked)
- Respects camera privacy (won't capture during video calls)
- Shows notifications for capture status
- Creates synthetic annotations if camera is active

### 4. **Statistics Tracking**
- Manual captures counted separately
- Shown in Statistics menu
- Tracks total manual vs automatic captures

---

## How to Use

### Method 1: Menu Bar
```
1. Click ⏱️ icon in menu bar
2. Click "📸 Capture Now (⌘⇧6)"
3. Screenshot captured immediately
```

### Method 2: Keyboard Shortcut
```
1. Press Cmd+Shift+6 anywhere on your Mac
2. Screenshot captured immediately
3. Notification shows status
```

---

## Setup Guide - Keyboard Shortcut

### Prerequisites

**macOS requires accessibility permissions for global hotkeys.**

### Step 1: Grant Accessibility Permission

1. Open **System Settings** / **System Preferences**
2. Go to **Security & Privacy** → **Privacy** → **Accessibility**
3. Click the lock icon 🔒 to make changes
4. Add the following (depending on how you run Chronometry):

**If running from Terminal:**
- ✅ Add `Terminal.app`

**If running as a service:**
- ✅ Add `Python.app` (usually at `/usr/local/bin/python3`)

**If running from IDE:**
- ✅ Add your IDE (e.g., `Cursor.app`, `Visual Studio Code.app`)

5. Click the lock icon 🔓 to prevent further changes
6. Restart the Chronometry menubar app

### Step 2: Test the Hotkey

1. Start Chronometry menubar: `./bin/start_chronometry_menubar.sh`
2. Check logs: You should see:
   ```
   INFO - Global hotkey registered: Cmd+Shift+6 for Capture Now
   ```
3. Press **Cmd+Shift+6**
4. You should see notification: "📸 Capturing screenshot now..."
5. Then: "✅ Screenshot saved: 20251009_123456.png"

### Step 3: Verify Capture

```bash
# Check that screenshot was saved
ls -ltr data/frames/$(date +%Y-%m-%d)/ | tail -1
```

---

## Technical Implementation

### 1. New Dependency: `pynput`

**File**: `requirements.txt`
```
pynput>=1.7.6
```

**Purpose**: Cross-platform library for monitoring and controlling keyboard/mouse

**Installation**:
```bash
cd /Users/pkasinathan/workspace/chronometry
source venv/bin/activate
pip install pynput>=1.7.6
```

### 2. New Function in `capture.py`

**Function**: `capture_single_frame(config, show_notifications=True)`

**Purpose**: Reusable function for capturing a single screenshot

**Features**:
- Screen lock detection
- Camera privacy detection
- Synthetic annotation creation
- Success/failure notifications
- Returns boolean success status

**Code Snippet**:
```python
def capture_single_frame(config: dict, show_notifications: bool = True) -> bool:
    """Capture a single screenshot immediately."""
    # Check screen lock
    if is_screen_locked():
        show_notification("Chronometry", "🔒 Screen is locked - skipping capture")
        return False
    
    # Check camera usage
    if is_camera_in_use():
        show_notification("Chronometry", "📹 Camera active - skipping for privacy")
        create_synthetic_annotation(...)
        return False
    
    # Capture screenshot
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(str(frame_path), "PNG")
    
    show_notification("Chronometry", f"✅ Screenshot saved: {frame_path.name}")
    return True
```

### 3. Menu Bar App Updates

**File**: `src/menubar_app.py`

**Changes**:
1. Added import: `from pynput import keyboard`
2. Added import: `capture_single_frame` from capture module
3. Added menu item: `"📸 Capture Now (⌘⇧6)"`
4. Added method: `capture_now(self, _=None)`
5. Added method: `setup_hotkey(self)`
6. Added stat tracking: `self.manual_captures`

**Menu Item**:
```python
rumps.MenuItem("📸 Capture Now (⌘⇧6)", callback=self.capture_now)
```

**Capture Method**:
```python
def capture_now(self, _=None):
    """Manually capture a screenshot immediately."""
    def run():
        success = capture_single_frame(self.config, show_notifications=True)
        if success:
            self.manual_captures += 1
    
    threading.Thread(target=run, daemon=True).start()
```

**Hotkey Setup**:
```python
def setup_hotkey(self):
    """Setup global hotkey listener for Cmd+Shift+6."""
    def on_activate():
        logger.info("Hotkey Cmd+Shift+6 pressed - triggering capture")
        self.capture_now()
    
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<cmd>+<shift>+6'),
        on_activate
    )
    
    keyboard_listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)
    )
    
    keyboard_listener.start()
```

---

## Use Cases

### 1. Important Discussion
```
📝 Scenario: Important Slack conversation about architecture
⌨️  Action: Press Cmd+Shift+6 to capture the discussion
✅ Result: Screenshot saved for later reference
```

### 2. Error Message
```
❌ Scenario: Rare error message appears
⌨️  Action: Press Cmd+Shift+6 before it disappears
✅ Result: Error captured for debugging
```

### 3. Design Review
```
🎨 Scenario: Looking at a design mockup that needs feedback
⌨️  Action: Press Cmd+Shift+6 to capture the design
✅ Result: Screenshot available for annotation
```

### 4. Demo Preparation
```
🎯 Scenario: Preparing demo, want specific screenshots
⌨️  Action: Navigate to each screen, press Cmd+Shift+6
✅ Result: Collection of demo screenshots
```

### 5. Meeting Notes
```
💼 Scenario: Important slide during video meeting (camera ON)
⌨️  Action: Press Cmd+Shift+6
✅ Result: Synthetic annotation created (respects privacy)
```

---

## Edge Cases Handled

### 1. Screen Locked
```
Input: Cmd+Shift+6 while screen is locked
Output: Notification "🔒 Screen is locked - skipping capture"
Result: No screenshot taken
```

### 2. Camera Active
```
Input: Cmd+Shift+6 during Zoom call
Output: Notification "📹 Camera active - skipping for privacy"
Result: Synthetic annotation created, no screenshot
```

### 3. No Accessibility Permission
```
Input: Cmd+Shift+6 without accessibility permission
Output: Hotkey doesn't trigger
Solution: Follow setup guide to grant permission
```

### 4. Rapid Fire
```
Input: Press Cmd+Shift+6 multiple times quickly
Output: Each press triggers a new capture thread
Result: Multiple screenshots captured
Note: Each runs in background, doesn't block UI
```

### 5. Capture Stopped
```
Input: Cmd+Shift+6 when automatic capture is stopped
Output: Manual capture still works!
Result: Screenshot saved regardless of capture state
```

---

## Benefits

### 1. **Flexibility**
- Capture on-demand in addition to periodic capture
- Works independently of automatic capture schedule
- No need to wait for next automatic capture

### 2. **Accessibility**
- Easy to use via menu or keyboard
- Global hotkey works from any application
- No need to switch to menubar

### 3. **Privacy Aware**
- Respects camera status
- Respects screen lock
- Creates synthetic annotations when appropriate

### 4. **Non-Disruptive**
- Runs in background thread
- Doesn't block UI
- Fast execution

### 5. **Trackable**
- Separate statistics for manual vs automatic
- Logged for debugging
- Visible in Statistics menu

---

## Files Modified

1. **requirements.txt**
   - Added: `pynput>=1.7.6`

2. **src/capture.py**
   - Added: `capture_single_frame()` function (76 lines)
   - Extracted reusable capture logic

3. **src/menubar_app.py**
   - Added import: `from pynput import keyboard`
   - Added import: `capture_single_frame`
   - Added menu item: "📸 Capture Now (⌘⇧6)"
   - Added method: `capture_now()` (24 lines)
   - Added method: `setup_hotkey()` (25 lines)
   - Added stat: `self.manual_captures`
   - Updated: `show_stats()` to include manual captures

---

## Testing

### Manual Test Plan

**Test 1: Menu Item Click**
```bash
1. Start menubar app
2. Click ⏱️ icon
3. Click "📸 Capture Now (⌘⇧6)"
4. Verify notification appears
5. Check data/frames/<today>/ for new file
Expected: ✅ Screenshot saved
```

**Test 2: Keyboard Shortcut**
```bash
1. Grant accessibility permission (see setup guide)
2. Start menubar app
3. Wait for log: "Global hotkey registered: Cmd+Shift+6"
4. Press Cmd+Shift+6
5. Verify notification appears
6. Check data/frames/<today>/ for new file
Expected: ✅ Screenshot saved
```

**Test 3: Screen Locked**
```bash
1. Lock screen (Cmd+Ctrl+Q)
2. Press Cmd+Shift+6 (from login screen if possible)
Expected: No screenshot, notification about locked screen
```

**Test 4: Camera Active**
```bash
1. Start Zoom/Google Meet (camera ON)
2. Press Cmd+Shift+6
3. Check for synthetic annotation JSON
Expected: No PNG, but JSON file created
```

**Test 5: Statistics**
```bash
1. Press Cmd+Shift+6 three times
2. Click ⏱️ → Statistics
3. Check "Manual Captures" count
Expected: Shows 3
```

---

## Troubleshooting

### Issue: Hotkey Doesn't Work

**Solution 1: Check Accessibility Permission**
```
System Settings → Security & Privacy → Privacy → Accessibility
Ensure Terminal/Python is checked
```

**Solution 2: Check Logs**
```bash
tail -f logs/menubar.log
# Look for: "Global hotkey registered: Cmd+Shift+6"
```

**Solution 3: Restart Menubar App**
```bash
./bin/stop_chronometry_menubar.sh
./bin/start_chronometry_menubar.sh
```

### Issue: Permission Denied on macOS

**Solution: Grant Input Monitoring Permission**
```
System Settings → Security & Privacy → Privacy → Input Monitoring
Add Terminal/Python
Restart menubar app
```

### Issue: No Notification Appears

**Solution: Check Notification Settings**
```
System Settings → Notifications → Python/Terminal
Enable: Alerts, Banner Style
```

---

## Future Enhancements (Optional)

1. **Customizable Hotkey**: Allow users to change the hotkey combination
2. **Multi-Monitor Selection**: Prompt which monitor to capture
3. **Region Selection**: Capture specific screen region
4. **Annotation Dialog**: Add immediate annotation/tag after capture
5. **Countdown Timer**: 3-2-1 countdown before capture
6. **Rapid Capture Mode**: Hold hotkey for burst capture
7. **Clipboard Integration**: Copy screenshot to clipboard

---

## Security Considerations

### Accessibility Permission
- Required for global hotkey
- Grants keyboard/mouse monitoring
- Be aware of security implications
- Only grant to trusted applications

### Privacy
- Respects camera status
- Respects screen lock
- No unauthorized captures
- User-initiated only

---

## Status

✅ **Complete and Ready to Use**
- Feature implemented
- Tested on macOS
- Documentation complete
- Setup guide provided

---

## Quick Start

```bash
# 1. Install dependency
cd /Users/pkasinathan/workspace/chronometry
source venv/bin/activate
pip install pynput>=1.7.6

# 2. Grant accessibility permission
# System Settings → Privacy → Accessibility → Add Terminal

# 3. Start menubar app
./bin/start_chronometry_menubar.sh

# 4. Test hotkey
# Press Cmd+Shift+6

# 5. Verify capture
ls -ltr data/frames/$(date +%Y-%m-%d)/ | tail -1
```

---

**Feature Added By**: AI Assistant  
**Date**: October 9, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready  

🎉 **Enjoy instant screenshot capture with Cmd+Shift+6!**

