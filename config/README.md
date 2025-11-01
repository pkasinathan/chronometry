# Chronometry Configuration Guide

## Overview

Chronometry uses a **split configuration system** with two files:

- **`user_config.yaml`** - User-customizable settings (exposed in UI Settings tab)
- **`system_config.yaml`** - System-level settings (advanced/internal, not in UI)

This separation ensures:
- Users only see/edit relevant settings
- Critical infrastructure configs are protected
- Clear distinction between user preferences and system requirements

---

## Configuration Files

### user_config.yaml (User-Editable)

These settings are **exposed in the web dashboard** at http://localhost:8051/ under Settings tab.

#### Capture Settings
```yaml
capture:
  capture_interval_seconds: 900  # How often to capture (15 min default)
  monitor_index: 1               # Which monitor (0=all, 1=primary, 2=secondary)
  retention_days: 1095           # Days to keep screenshots (3 years)
```

#### Annotation Settings
```yaml
annotation:
  batch_size: 4                  # Images per AI analysis batch
  prompt: "Summarize the..."     # AI prompt for screenshot analysis
```

#### Digest Settings
```yaml
digest:
  interval_seconds: 3600         # Digest generation frequency (1 hour)
  ncp_project_id: "yourproject"  # Your Copilot project ID
```

#### Timeline Settings
```yaml
timeline:
  bucket_minutes: 30             # Activity grouping window
  exclude_keywords: []           # Keywords to hide from timeline
```

#### Notification Settings
```yaml
notifications:
  enabled: true                  # Enable desktop notifications
  notify_before_capture: true    # Show notification before each capture
```

---

### system_config.yaml (System-Level)

These settings are **NOT exposed in the UI** and should only be edited by advanced users.

#### Server Settings
```yaml
server:
  host: "0.0.0.0"               # Server host (0.0.0.0 = all interfaces)
  port: 8051                    # Web dashboard port
  debug: true                   # Debug mode
  secret_key: "..."             # Flask session secret
```

#### API Configuration
```yaml
annotation:
  api_url: "https://..."        # Metatron API endpoint for screenshots
  metatron_command: "metatron"  # Command to run
  metatron_app: "aiopsproxy"    # App name for authentication
  timeout_sec: 30               # API timeout
  json_suffix: ".json"          # Annotation file extension

digest:
  enabled: true                 # Enable digest generation
  api_url: "https://..."        # Copilot API endpoint
  metatron_app: "copilotdpjava" # App name for authentication
  model: "gpt-4o"               # AI model
  temperature: 0.7              # Model temperature
  max_tokens_default: 500       # Default token limit
  max_tokens_category: 200      # Tokens for category summaries
  max_tokens_overall: 300       # Tokens for overall summary
```

#### Internal Settings
```yaml
paths:
  root_dir: "./data"            # Data storage directory
  output_dir: "./output"        # HTML output directory
  logs_dir: "./logs"            # Log files directory

capture:
  region: null                  # Custom region [x,y,w,h] or null
  startup_delay_seconds: 5      # Delay before first capture
  screen_check_timeout: 2       # Timeout for lock detection

timeline:
  gap_minutes: 5                # Activity merging tolerance
  generation_interval_seconds: 300  # Timeline update frequency
  title: "Chronometry Timeline"     # HTML page title

logging:
  level: "INFO"                 # Log level
  format: "%(asctime)s..."      # Log format string
```

---

## How Configuration Works

### 1. Loading Priority

The system tries to load configs in this order:

1. **Split mode** (preferred):
   - Loads `user_config.yaml`
   - Loads `system_config.yaml`
   - Merges them (user overrides system)

2. **Legacy mode** (fallback):
   - If split files don't exist, loads `config.yaml`
   - Shows deprecation warning

### 2. Merging Behavior

When both config files exist:
- System config provides defaults
- User config overrides matching keys
- Nested dictionaries are deep-merged

Example:
```yaml
# system_config.yaml
capture:
  capture_interval_seconds: 900
  monitor_index: 1
  region: null

# user_config.yaml
capture:
  capture_interval_seconds: 600  # Override: capture every 10 min

# Result (merged):
capture:
  capture_interval_seconds: 600  # From user
  monitor_index: 1               # From system
  region: null                   # From system
```

### 3. Validation

All configs are validated on load:
- Type checking (int, float, string, bool, list)
- Range validation (positive numbers, non-negative, etc.)
- Required field checking
- Helpful error messages if invalid

---

## Editing Configuration

### Via Web UI (Recommended)

1. Open dashboard: http://localhost:8051/
2. Click **Settings** tab
3. Modify values
4. Click **Save Changes**
5. Restart services for changes to take effect

### Via File Editor (Advanced)

1. Edit `config/user_config.yaml` directly
2. Save the file
3. Restart services: `./bin/manage_services.sh restart`

**Important**: Only edit `system_config.yaml` if you know what you're doing!

---

## Migration from Old config.yaml

If you have an old `config.yaml` file:

### Option 1: Automatic Migration (Manual Split)

1. **Backup** your current config:
   ```bash
   cp config/config.yaml config/config.yaml.backup
   ```

2. **Extract user settings** to `user_config.yaml`:
   ```yaml
   capture:
     capture_interval_seconds: 900
     monitor_index: 1
     retention_days: 1095
   annotation:
     batch_size: 4
     prompt: "Your custom prompt..."
   digest:
     interval_seconds: 3600
     ncp_project_id: "yourproject"
   timeline:
     bucket_minutes: 30
     exclude_keywords: []
   notifications:
     enabled: true
     notify_before_capture: true
   ```

3. **Copy** `system_config.yaml` from this repo (already has defaults)

4. **Test** the split configs work:
   ```bash
   ./bin/manage_services.sh restart
   ./bin/manage_services.sh status
   ```

5. **Archive** old config.yaml:
   ```bash
   mv config/config.yaml config/config.yaml.old
   ```

### Option 2: Keep Legacy Mode

Just keep using `config.yaml` - it still works! You'll see a deprecation warning in logs, but everything functions normally.

---

## Troubleshooting

### "No configuration files found" Error

**Cause**: Neither split configs nor legacy config.yaml exists.

**Fix**: Create at least one:
- Copy `user_config.yaml` and `system_config.yaml` from repo, OR
- Restore `config.yaml` from backup

### Settings Don't Save in UI

**Cause**: Validation failed or file permissions issue.

**Fix**:
1. Check browser console for validation errors
2. Ensure `config/user_config.yaml` is writable:
   ```bash
   chmod 644 config/user_config.yaml
   ```

### Services Won't Start After Config Change

**Cause**: Invalid configuration value.

**Fix**:
1. Check logs: `./bin/manage_services.sh logs`
2. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/user_config.yaml'))"
   ```
3. Restore from backup if needed

### Changes Don't Take Effect

**Cause**: Services need restart to reload config.

**Fix**:
```bash
./bin/manage_services.sh restart
```

---

## Config Reference

### Capture Interval Examples

| Seconds | Minutes | Use Case |
|---------|---------|----------|
| 300 | 5 min | High frequency (detailed tracking) |
| 600 | 10 min | Medium frequency (balanced) |
| 900 | 15 min | Default (good balance) |
| 1800 | 30 min | Low frequency (light tracking) |
| 3600 | 1 hour | Very low (periodic snapshots) |

### Digest Interval Examples

| Seconds | Time | Use Case |
|---------|------|----------|
| 1800 | 30 min | Frequent updates |
| 3600 | 1 hour | Default (recommended) |
| 7200 | 2 hours | Less frequent |
| 14400 | 4 hours | Infrequent |

### Retention Days Examples

| Days | Duration | Use Case |
|------|----------|----------|
| 7 | 1 week | Short-term review only |
| 30 | 1 month | Monthly analysis |
| 365 | 1 year | Annual tracking |
| 1095 | 3 years | Default (long-term analysis) |

---

## Best Practices

### 1. Start Conservative
- Use default capture_interval (900s = 15 min)
- Adjust based on your workflow
- Monitor disk usage

### 2. Customize AI Prompt
- Tailor the annotation prompt to your work context
- Include specific apps/tools you use
- Examples: "Slack", "JIRA", "VS Code", "Zoom"

### 3. Use Exclude Keywords
- Filter out distractions from timeline
- Common examples: youtube, reddit, twitter, facebook
- Case-insensitive matching

### 4. Backup Before Major Changes
```bash
cp config/user_config.yaml config/user_config.yaml.backup
```

### 5. Test After Changes
```bash
./bin/manage_services.sh restart
./bin/manage_services.sh status
```

---

## Support

- **Documentation**: README.md, QUICK_START.md
- **Logs**: `./logs/` directory
- **Validation**: Built-in on config load
- **UI Help**: Hover over ⓘ icons in Settings tab

---

**Last Updated**: 2025-11-01
