# Configuration Files

All configuration files for Chronometry.

## Files

### `config.yaml`
Main configuration file for all Chronometry modules.

**Sections:**
- `capture` - Screen capture settings (FPS, monitor, retention)
- `annotation` - AI annotation settings (API, batch size)
- `timeline` - Timeline generation settings
- `digest` - Daily digest settings (interval, NCP project ID)

**Location:** `config/config.yaml`  
**Loaded by:** All Python modules via `common.load_config()`

### `com.chronometry.menubar.plist`
LaunchAgent configuration for menubar app.

**Installed to:** `~/Library/LaunchAgents/`  
**Manages:** Menubar application as a service

### `com.chronometry.webserver.plist`
LaunchAgent configuration for web server.

**Installed to:** `~/Library/LaunchAgents/`  
**Manages:** Web dashboard server on port 8051

## Editing Configuration

### Via Web UI (Recommended)
```
http://localhost:8051 → Settings tab
```

### Via File (Advanced)
```bash
vi config/config.yaml
```

Then restart services:
```bash
./manage_services.sh restart
```

## Service Installation

To install plist files as LaunchAgents:
```bash
./manage_services.sh install
```

This copies plist files from `config/` to `~/Library/LaunchAgents/`

