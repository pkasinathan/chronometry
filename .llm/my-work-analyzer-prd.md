# MyWorkAnalyzer PRD (v0.2.1)

## Vision
A **production-ready**, private screen capture and analysis tool that runs locally.  
Captures screenshots at configurable intervals, annotates them using Netflix's internal Metatron `/images/summarize` endpoint, and visualizes the day with a beautiful, **Netflix-themed interactive timeline**.  
Built with security, reliability, and modern UI/UX in mind.

---

## Goals

### **Mandatory - Core Functionality**

1. **Screen Capture**  
   - Take screenshots at a configurable FPS (default: 0.033 = 1 per 30 seconds).  
   - Save as `.png` into `data/frames/YYYY-MM-DD/`.  
   - Support configurable monitor index or custom screen region.
   - **Error Recovery**: Continue capturing even if individual frames fail.
   - **Automatic Cleanup**: Delete frames older than N days (configurable retention).

2. **Annotation**  
   - Batch size configurable (e.g., 1–5 images per API call).  
   - Use configurable Metatron API endpoint + prompt via `metatron` CLI tool.
   - **Retry Logic**: Exponential backoff (3 attempts: 1s, 2s, 4s delays).
   - Request format:  
     ```json
     {
       "prompt": "Summarize the type of task or activity shown...",
       "files": [
         { "name": "frame0", "content_type": "image/png", "base64_data": "..." }
       ]
     }
     ```  
   - Store output JSON (`summary`, `sources`) as separate `.json` files next to PNGs.  
     Example: `20251003_103000.png` → `20251003_103000.json`.
   - **API Response Validation**: Ensure response contains required fields with defaults.

3. **Visualization**  
   - **Netflix-Themed Timeline**: Modern, clean interface with Netflix red accents.
   - Bucket size configurable (default: 15 minutes).  
   - Parse JSON summaries, group by time buckets, render interactive Plotly timeline.
   - **8 Time Range Buttons**: 1h, 4h, 8h, 24h, 2d, 3d, 5d, All.
   - **Text-Wrapped Hover Tooltips**: Smart wrapping at 60 characters per line.
   - **Statistics Dashboard**: Display total frames, time periods, and averages.
   - **Responsive Design**: Works on desktop and mobile devices.
   - **Smooth Animations**: Fade-in effects and hover transitions.

### **Mandatory - Security & Reliability**

4. **Security**
   - **URL Validation**: Prevent command injection by validating API URLs (must be http/https).
   - **Configuration Validation**: Comprehensive validation with detailed error messages at startup.
   - **Path Safety Checks**: Ensure cleanup operations stay within project directory.
   - **Input Validation**: All config values validated for type and range.

5. **Error Handling**
   - **Structured Logging**: Replace all print statements with proper logging (INFO, WARNING, ERROR).
   - **Graceful Failure Recovery**: Individual capture/annotation failures don't crash the process.
   - **Retry Logic**: Exponential backoff for API calls (3 attempts).
   - **Error Counter**: Exit capture after 5 consecutive failures.
   - **Detailed Error Messages**: Provide actionable error information.

6. **Code Quality**
   - **Type Hints**: Comprehensive type annotations (~80% coverage).
   - **Docstrings**: Every function documented with Args, Returns, Raises.
   - **No Code Duplication**: Extract shared utilities (e.g., `get_monitor_config`).
   - **Consistent Patterns**: Uniform error handling and logging throughout.

### **Mandatory - Testing & Documentation**

7. **Testing**
   - **Unit Tests**: Basic test coverage (~40%) with pytest framework.
   - **Test Fixtures**: Sample configuration and test data.
   - **Mock Testing**: For API calls and external dependencies.
   - **Quick Test Script**: End-to-end verification with mock data.

8. **Documentation**
   - **Comprehensive README**: Installation, usage, troubleshooting, features.
   - **CHANGELOG**: Version history with detailed release notes.
   - **Inline Documentation**: Comments explaining complex logic.
   - **Configuration Comments**: Every config option documented in `config.yaml`.

### **Optional / Nice-to-have**
- Pause/resume functionality (check for pause flag file).
- Blur/redaction regions for privacy (rectangles defined in config).
- Date range timeline generation.
- Multi-day timeline combination.
- Light/dark theme toggle.
- Export timeline as PDF/PNG.
- Search and filter activities.

---

## Non-Goals
- No database — only flat files (PNG + JSON).  
- No heavy local AI inference.  
- No calendar/journaling/distraction scoring.  
- No external APIs besides Metatron.

---

## Deliverables

### **Core Modules**
- `capture.py` → Screen capture with error recovery and logging.  
- `annotate.py` → Encode PNGs, call Metatron API with retry logic, save JSON.  
- `timeline.py` → Generate Netflix-themed timeline with modern UI.  
- `common.py` → Shared utilities (config validation, directories, monitor setup, cleanup).  
- `quick_test.py` → End-to-end test script with mock annotations.

### **Configuration & Setup**
- `config.yaml` → Master configuration file with all options documented.  
- `requirements.txt` → Runtime dependencies.
- `requirements-dev.txt` → Development and testing dependencies.
- `.gitignore` → Clean repository (exclude venv, data, output, caches).

### **Automation**
- `start_myworkanalyzer_agent.sh` → Shell script to run capture + periodic annotation/timeline.

### **Testing**
- `tests/test_common.py` → Unit tests for common utilities.
- `tests/test_annotate.py` → Unit tests for annotation module.
- `tests/fixtures/config_test.yaml` → Test configuration.
- `tests/README.md` → Testing documentation.

### **Documentation**
- `README.md` → Complete usage guide with features, installation, troubleshooting.
- `CHANGELOG.md` → Version history and release notes.

---

## Example `config.yaml`

```yaml
# Base directory where all data is stored
root_dir: "./data"

# Capture settings
capture:
  fps: 0.033  # 1 frame per 30 seconds
  monitor_index: 1  # 0 = all monitors, 1+ = specific monitor
  region: null  # [x, y, width, height] or null for full screen
  retention_days: 3  # Auto-delete frames older than N days

# Annotation settings
annotation:
  # NOTE: Port 7004 is required for Metatron proxy
  api_url: "https://aiopsproxy.cluster.us-east-1.prod.cloud.netflix.net:7004/images/summarize"
  prompt: "Summarize the type of task or activity shown in these images using clear, work-related terms."
  batch_size: 1  # Number of images per API request
  timeout_sec: 30  # Command timeout
  json_suffix: ".json"  # Extension for annotation files

# Visualization settings
timeline:
  bucket_minutes: 15  # Time bucket size for grouping activities
  min_tokens_per_bucket: 10  # Minimum word count to include bucket
  title: "My Work Analyzer Timeline"
  output_dir: "./output"
  include_keywords: []  # Only show buckets with these keywords (empty = no filter)
  exclude_keywords: []  # Hide buckets with these keywords
  style:
    height: 900  # Timeline height in pixels
    theme: "light"  # "light" or "dark" (both use Netflix styling)
```

---

## Technical Requirements

### **Dependencies**
- Python 3.11+
- `mss` - Cross-platform screenshot capture
- `pillow` - Image processing
- `plotly` - Interactive timeline visualization
- `pandas` - Data manipulation
- `pyyaml` - Configuration parsing
- `metatron` CLI tool (Netflix internal) - API authentication

### **Development Dependencies**
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mock testing
- `black`, `flake8`, `mypy` - Code quality tools

### **System Requirements**
- macOS, Linux, or Windows
- Network access to Netflix internal services
- Metatron CLI tool installed and configured

---

## Architecture & Design

### **Module Responsibilities**
1. **capture.py**: Screen capture loop with error recovery
2. **annotate.py**: Batch image encoding and API calls with retry
3. **timeline.py**: Data aggregation and visualization generation
4. **common.py**: Shared utilities and validation
5. **quick_test.py**: Integration testing

### **Data Flow**
```
Screenshot → PNG file → Base64 encode → Metatron API → JSON file → Timeline HTML
   (capture.py)  →  (annotate.py)  →  (timeline.py)
```

### **Error Handling Strategy**
- **Capture**: Continue on individual failures, exit after 5 consecutive errors
- **Annotation**: Retry with exponential backoff (3 attempts), log and skip on failure
- **Timeline**: Validate data, skip invalid entries, generate with available data

### **Security Measures**
- URL validation before subprocess calls
- Configuration validation at startup
- Path safety checks for file operations
- No sensitive data in logs or error messages

---

## UI/UX Specifications

### **Netflix-Themed Timeline Design**

**Color Palette:**
- Background: `#0a0a0a` (deep black)
- Card Background: `#1a1a1a` (dark gray)
- Borders: `#2a2a2a` (subtle gray)
- Primary Accent: `#E50914` (Netflix red)
- Text: `#ffffff` (white), `#8c8c8c` (gray)

**Layout:**
- **Header**: Centered title with Netflix red, date subtitle
- **Stats Bar**: 3-column CSS Grid with hover effects
- **Chart Container**: Dedicated card with shadow and padding
- **Footer**: Version info and timestamp

**Interactive Elements:**
- **Stat Cards**: Lift 4px on hover, red accent line appears
- **Time Range Buttons**: 8 Netflix red buttons (1h, 4h, 8h, 24h, 2d, 3d, 5d, All)
- **Hover Tooltips**: Text-wrapped at 60 chars, Netflix dark background, red border
- **Animations**: Smooth 0.3s cubic-bezier transitions, fade-in on page load

**Typography:**
- Font: System native (`-apple-system, BlinkMacSystemFont, Segoe UI`)
- Title: 42px, weight 700, Netflix red
- Stats: 36px values, 13px labels, uppercase
- Body: 13-15px, weight 400

**Responsive:**
- Desktop: 1400px max-width container
- Mobile: Single column stats, reduced padding
- All devices: Smooth scrolling with Netflix red scrollbars

---

## Success Criteria

### **Functional**
- ✅ Can run `python capture.py` → frames saved with error recovery
- ✅ Can run `python annotate.py` → JSON summaries with retry logic
- ✅ Can run `python timeline.py` → Netflix-themed HTML timeline
- ✅ Can run `./start_myworkanalyzer_agent.sh` → automated workflow
- ✅ Can run `python quick_test.py` → end-to-end verification

### **Quality**
- ✅ Zero security vulnerabilities
- ✅ All critical errors handled gracefully
- ✅ Structured logging throughout
- ✅ 40%+ test coverage
- ✅ No linter errors
- ✅ Comprehensive documentation

### **User Experience**
- ✅ Beautiful, modern Netflix-themed interface
- ✅ Text-wrapped hover tooltips for readability
- ✅ 8 time range options for quick navigation
- ✅ Interactive stats dashboard
- ✅ Smooth animations and transitions
- ✅ Responsive design for all devices

### **Reliability**
- ✅ Survives individual capture failures
- ✅ Retries API calls automatically
- ✅ Validates configuration at startup
- ✅ Prevents command injection attacks
- ✅ Safe file system operations

---

## Version History

- **v0.2.1** (Current) - Netflix-themed UI, text-wrapped tooltips, 8 time ranges
- **v0.2.0** - Security fixes, error recovery, retry logic, logging, testing
- **v0.1.0** - Initial MVP with basic capture, annotation, timeline

---

## Deployment Checklist

Before deploying:
1. ✅ Run `pytest` - all tests pass
2. ✅ Run `python quick_test.py` - end-to-end works
3. ✅ Check `config.yaml` - API URL includes port 7004
4. ✅ Verify `metatron` CLI tool installed
5. ✅ Review `README.md` - documentation up to date
6. ✅ Check `.gitignore` - no sensitive data committed

---

**Status:** ✅ Production Ready  
**Version:** 0.2.1  
**Last Updated:** October 2025
