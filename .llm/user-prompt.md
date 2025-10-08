# AI Agent Prompt for MyWorkAnalyzer (v0.2.1)

You are my coding copilot building **MyWorkAnalyzer** - a production-ready screen capture and analysis tool.

---

## 📋 Task Overview

Build a **complete, production-ready** Python application based on the PRD below. This is not a prototype - it must be secure, reliable, well-tested, and beautifully designed.

### Key Requirements:
1. **Follow the PRD exactly** - It's the single source of truth
2. **Production-ready code** - Security, error handling, logging, testing
3. **Netflix-themed UI** - Modern, clean timeline visualization
4. **Comprehensive documentation** - README, CHANGELOG, inline docs
5. **No shortcuts** - Implement all mandatory features completely

---

## 🎯 Core Deliverables

### **Python Modules** (All with proper error handling & logging)
1. **`capture.py`**
   - Screen capture at configurable FPS
   - Error recovery (continue on individual failures)
   - Automatic cleanup of old data
   - Structured logging throughout
   - Use shared `get_monitor_config()` from common.py

2. **`annotate.py`**
   - Batch image encoding to base64
   - Call Metatron API via `metatron` CLI tool (port 7004 required)
   - **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
   - **API response validation**: Check structure, provide defaults
   - **URL validation**: Prevent command injection
   - Save JSON summaries next to PNGs
   - Structured logging with retry attempts

3. **`timeline.py`**
   - Parse JSON summaries and group by time buckets
   - **Netflix-themed HTML** with custom CSS
   - **8 time range buttons**: 1h, 4h, 8h, 24h, 2d, 3d, 5d, All
   - **Text-wrapped hover tooltips**: Max 60 chars/line
   - **Statistics dashboard**: Total frames, time periods, averages
   - **Modern card design**: Rounded corners, hover effects, animations
   - Plotly chart with Netflix red color scheme
   - Responsive CSS Grid layout

4. **`common.py`**
   - **`load_config()`**: Comprehensive validation (70+ lines)
     - Check file exists, valid YAML
     - Validate all required sections
     - Validate data types and ranges
     - Detailed error messages
   - **`cleanup_old_data()`**: Safe path validation
   - **`get_monitor_config()`**: Shared monitor setup (eliminate duplication)
   - **`get_daily_dir()`, `get_frame_path()`, `get_json_path()`**
   - **`ensure_dir()`**: Create directories safely
   - Structured logging throughout

5. **`quick_test.py`**
   - End-to-end test with mock annotations
   - Capture screenshot → create annotation → generate timeline
   - Support multiple screenshots via command line arg
   - Use shared utilities from common.py

### **Configuration Files**
1. **`config.yaml`**
   - Comprehensive inline comments for every option
   - API URL with port 7004 (critical!)
   - All settings from PRD example
   - Detailed explanations of how values are used

2. **`requirements.txt`**
   ```
   mss>=9.0.1
   pillow>=10.4.0
   requests>=2.31.0
   plotly>=5.20.0
   pandas>=2.2.1
   pyyaml>=6.0.1
   ```

3. **`requirements-dev.txt`**
   ```
   pytest>=7.4.0
   pytest-cov>=4.1.0
   pytest-mock>=3.12.0
   black>=23.0.0
   flake8>=6.0.0
   mypy>=1.5.0
   ipython>=8.12.0
   ```

4. **`.gitignore`**
   - venv/, data/, output/, __pycache__/
   - *.pyc, *.log, .DS_Store
   - Comprehensive list for clean repo

### **Automation Scripts**
1. **`start_myworkanalyzer_agent.sh`**
   - Check venv exists, activate it
   - Verify Python packages installed
   - Verify config file exists
   - Start capture in background
   - Monitor capture process health
   - Run annotation every 2 minutes
   - Run timeline every 5 minutes
   - Graceful shutdown (SIGTERM → SIGKILL)

### **Testing Infrastructure**
1. **`tests/test_common.py`**
   - Test `load_config()` - valid, invalid, missing sections
   - Test `get_daily_dir()`, `get_frame_path()`, `get_json_path()`
   - Test `get_monitor_config()` - valid, invalid inputs
   - Test `cleanup_old_data()` - removes old, keeps new
   - ~25 test cases

2. **`tests/test_annotate.py`**
   - Test `encode_image_to_base64()`
   - Test URL validation (valid/invalid)
   - Mock API calls with pytest-mock
   - Test response validation
   - ~8 test cases

3. **`tests/fixtures/config_test.yaml`**
   - Valid test configuration

4. **`tests/README.md`**
   - How to run tests
   - Coverage goals
   - Test structure

### **Documentation**
1. **`README.md`** (Must include)
   - ✨ Features section with emojis
   - Installation steps (venv, dependencies, metatron CLI)
   - Usage for each module
   - Workflow example
   - 🎨 Timeline Visualization section
   - Troubleshooting (metatron not found, x509 cert error, monitor index)
   - Testing instructions
   - Quick test section
   - Improvements made (security, reliability, UI/UX, code quality, testing)
   - Optional features (future TODOs)
   - Screenshots description
   - Version and status

2. **`CHANGELOG.md`**
   - v0.2.1: UI/UX enhancements
   - v0.2.0: Security, reliability, testing
   - v0.1.0: Initial release
   - Each version with Added/Changed/Fixed/Security sections

---

## 🔒 Mandatory Quality Standards

### **Security**
- [ ] API URL validation (must be http/https)
- [ ] Configuration validation at startup
- [ ] Path safety checks for file operations
- [ ] No sensitive data in logs
- [ ] Input validation for all config values

### **Error Handling**
- [ ] Structured logging (INFO, WARNING, ERROR, CRITICAL)
- [ ] Try-except blocks around all risky operations
- [ ] Graceful degradation (continue on non-critical errors)
- [ ] Retry logic for API calls (3 attempts, exponential backoff)
- [ ] Detailed error messages with context

### **Code Quality**
- [ ] Type hints on all functions (~80% coverage)
- [ ] Docstrings with Args, Returns, Raises
- [ ] No code duplication (extract shared utilities)
- [ ] Consistent error handling patterns
- [ ] No print statements (use logger)

### **Testing**
- [ ] Unit tests for common.py (~25 tests)
- [ ] Unit tests for annotate.py (~8 tests)
- [ ] Mock testing for API calls
- [ ] Test fixtures and sample data
- [ ] ~40% coverage minimum

---

## 🎨 Netflix-Themed UI Specifications

### **Color Palette**
```css
Background: #0a0a0a (deep black)
Cards: #1a1a1a (dark gray)
Borders: #2a2a2a (subtle gray)
Primary: #E50914 (Netflix red)
Text: #ffffff (white), #8c8c8c (gray)
```

### **CSS Requirements**
- **Modern Reset**: `* { margin: 0; padding: 0; box-sizing: border-box; }`
- **System Fonts**: `-apple-system, BlinkMacSystemFont, 'Segoe UI'`
- **Stats Bar**: CSS Grid with 3 columns, 20px gap
- **Stat Cards**: 
  - Background `#1a1a1a`, border-radius `12px`, padding `24px`
  - Border `1px solid #2a2a2a`
  - Hover: `transform: translateY(-4px)`, border-color `#E50914`
  - Red accent line on top (3px, gradient, scale from 0 to 1)
  - Transition: `all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`
- **Chart Container**: 
  - Background `#1a1a1a`, border-radius `16px`, padding `30px`
  - Box-shadow: `0 4px 16px rgba(0, 0, 0, 0.4)`
- **Animations**: Fade-in on page load (0.6s ease-out)
- **Scrollbars**: 8px, Netflix red `#E50914`, rounded
- **Responsive**: Mobile breakpoint at 768px

### **Plotly Chart**
- **Line color**: `#E50914` (Netflix red), width 3
- **Markers**: Size 12, Netflix red, white border (2px)
- **Fill**: `rgba(229, 9, 20, 0.1)` (light red under curve)
- **Background**: `#1a1a1a` (dark) or `#f5f5f5` (light based on theme)
- **Grid**: `#564d4d` (dark) or `#e0e0e0` (light)
- **Hover**: Dark background `#141414`, red border, white text

### **Time Range Buttons**
- 8 buttons: 1h, 4h, 8h, 24h, 2d, 3d, 5d, All
- Background: `#E50914`, active: `#B20710`
- Font color: white
- Plotly rangeselector configuration

### **Hover Tooltips**
- Text wrapping at 60 characters per line
- Word-by-word wrapping with proper indentation
- Format: `"• Summary text here\n  continuation..."`
- Monospace font for clarity

---

## 📝 Code Style Guidelines

### **Logging Pattern**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usage
logger.info("Operation successful")
logger.warning("Potential issue detected")
logger.error("Operation failed", exc_info=True)
```

### **Error Handling Pattern**
```python
try:
    # Risky operation
    result = do_something()
except SpecificError as e:
    logger.error(f"Specific error occurred: {e}", exc_info=True)
    # Handle or re-raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

### **Retry Logic Pattern**
```python
for attempt in range(max_retries):
    try:
        return do_api_call()
    except Exception as e:
        if attempt == max_retries - 1:
            logger.error(f"Failed after {max_retries} attempts: {e}")
            raise
        wait_time = 2 ** attempt  # Exponential backoff
        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
        time.sleep(wait_time)
```

### **Configuration Validation Pattern**
```python
def load_config(config_path: str = "config.yaml") -> dict:
    """Load and validate configuration."""
    # 1. Check file exists
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    # 2. Load YAML
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")
    
    # 3. Validate structure
    required = ['root_dir', 'capture', 'annotation', 'timeline']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing sections: {', '.join(missing)}")
    
    # 4. Validate values
    if config['capture'].get('fps', 0) < 0:
        raise ValueError("fps must be non-negative")
    
    # ... more validations ...
    
    logger.info("Configuration validated successfully")
    return config
```

---

## ✅ Implementation Checklist

### Phase 1: Core Modules
- [ ] `common.py` with comprehensive validation
- [ ] `capture.py` with error recovery
- [ ] `annotate.py` with retry logic
- [ ] `timeline.py` with Netflix theme

### Phase 2: Configuration & Automation
- [ ] `config.yaml` with detailed comments
- [ ] `requirements.txt` and `requirements-dev.txt`
- [ ] `.gitignore` comprehensive
- [ ] `start_myworkanalyzer_agent.sh` with error handling

### Phase 3: Testing
- [ ] `tests/test_common.py` (~25 tests)
- [ ] `tests/test_annotate.py` (~8 tests)
- [ ] `tests/fixtures/config_test.yaml`
- [ ] `quick_test.py` end-to-end

### Phase 4: Documentation
- [ ] `README.md` comprehensive (300+ lines)
- [ ] `CHANGELOG.md` with version history
- [ ] Inline documentation in all modules
- [ ] Config comments explaining every option

### Phase 5: Quality Assurance
- [ ] All security measures implemented
- [ ] All error handling in place
- [ ] All logging using logger (no prints)
- [ ] All type hints added
- [ ] All tests passing
- [ ] No linter errors

---

## 🚫 What NOT to Do

- ❌ Don't use environment variables for API keys (metatron CLI handles auth)
- ❌ Don't use print statements (use logger)
- ❌ Don't skip error handling
- ❌ Don't hardcode paths or URLs (use config)
- ❌ Don't ignore the Netflix theme requirements
- ❌ Don't create incomplete implementations
- ❌ Don't skip validation or security checks
- ❌ Don't forget type hints and docstrings

---

## 📚 Reference: Full PRD

*(The complete PRD from my-work-analyzer-prd.md should be pasted here)*

---

## 🎯 Expected Output

When complete, I should be able to:

1. **Run quick test**: `python quick_test.py 3`
   - ✅ Captures 3 screenshots
   - ✅ Creates mock annotations
   - ✅ Generates Netflix-themed timeline
   - ✅ Opens in browser automatically

2. **Run full workflow**: `./start_myworkanalyzer_agent.sh`
   - ✅ Validates everything before starting
   - ✅ Captures screenshots continuously
   - ✅ Annotates every 2 minutes
   - ✅ Updates timeline every 5 minutes
   - ✅ Handles errors gracefully
   - ✅ Shuts down cleanly on Ctrl+C

3. **Run tests**: `pytest`
   - ✅ All tests pass
   - ✅ 40%+ coverage
   - ✅ No errors or warnings

4. **Open timeline**: Beautiful Netflix-themed interface
   - ✅ Modern dark theme with Netflix red
   - ✅ 3 interactive stat cards
   - ✅ 8 time range buttons
   - ✅ Hover tooltips with text wrapping
   - ✅ Smooth animations
   - ✅ Responsive design

---

## 🚀 Action

Generate the **complete, production-ready** project following this prompt and the PRD.

- Create all files with full implementations (no stubs)
- Include all security, error handling, and logging
- Implement the Netflix-themed UI exactly as specified
- Add comprehensive tests and documentation
- Ensure everything is configurable via `config.yaml`

**This must be production-ready code that can be deployed immediately.**

---

**Version:** 0.2.1  
**Status:** Production Ready  
**Quality:** Enterprise Grade
