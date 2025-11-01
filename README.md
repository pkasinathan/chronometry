# Chronometry

*The Science of Your Time*

A privacy-first, AI-powered work activity analyzer that automatically captures, annotates, and summarizes your daily work. Features a beautiful web dashboard with real-time updates and AI-generated daily digests.

## ✨ What's New

### 🤖 **AI-Powered Daily Digest**
- Automatic daily summaries generated via Netflix Copilot API (GPT-4o)
- Category-based activity breakdowns
- Professional, readable summaries of your work
- Integrated into main process - no separate scheduler needed

### 🌐 **Modern Web Dashboard**
- Real-time web interface on `http://localhost:8051`
- 5 interactive tabs: Dashboard, Timeline, Analytics, Search, Settings
- Auto-refreshes every 60 seconds
- Netflix-inspired dark theme
- Fully responsive design

### 🎯 **Streamlined Architecture**
- Digest generation integrated into capture/annotation loop
- 6 shell scripts organized in 3 start/stop pairs
- Unified configuration via web UI
- Simplified process management

---

## 🚀 Features

### Core Functionality
- **📸 Automatic Screen Capture** - Configurable intervals (default: every 15 minutes)
- **⚡ Capture Now (Cmd+Shift+6)** - Manual ad-hoc screenshots with global hotkey
- **🤖 AI Annotation** - Batch processing via Metatron API (default: 4 frames together)
- **📋 Daily Digest** - AI-powered daily summaries via Copilot API (GPT-4o)
- **📊 Interactive Timeline** - Smart batch grouping with markdown-formatted summaries
- **📈 Analytics Dashboard** - Charts, insights, and productivity metrics
- **🔍 Search** - Full-text search through all activities
- **⚙️ Settings** - Configure everything via web UI (live updates)

### Privacy & Security
- **🔒 100% Local Storage** - All data stored on your machine
- **⚠️ 5-Second Warning** - Notification before capture starts
- **📸 Pre-Capture Alerts** - Notification before every screenshot
- **🔒 Screen Lock Detection** - Auto-skips when screen is locked
- **📹 Camera Privacy Protection** - Auto-pauses during video calls (NEW!)
- **🎯 Synthetic Annotations** - Tracks meeting time without screenshots
- **⏸️ Easy Pause/Resume** - One-click pause for sensitive work
- **🗑️ Auto-Cleanup** - Configurable data retention (default: 3 years)

### User Interfaces

#### 1. **Web Dashboard** (Port 8051) 🌐
```
📊 Dashboard  - Today's AI Digest + Quick Stats
📅 Timeline   - Detailed activity timeline
📈 Analytics  - Productivity charts and insights
🔍 Search     - Search all activities
⚙️  Settings  - Configure capture, digest, etc.
```

#### 2. **macOS Menu Bar App** ⏱️
```
Start/Stop, Pause/Resume, Manual triggers,
Quick access to dashboard and timelines
```

#### 3. **Command Line** 💻
```
Full control via terminal scripts
```

---

## 📦 Installation

### Quick Install (Recommended)

Use the service manager - it handles everything automatically:

```bash
git clone https://github.netflix.net/pkasinathan/chronometry.git
cd chronometry
./bin/manage_services.sh install
```

**What it does**:
- ✅ Auto-creates virtual environment if missing
- ✅ Installs all dependencies from requirements.txt
- ✅ Processes plist templates with your project path
- ✅ Installs services to run at boot
- ✅ Starts services immediately

### Pre-requisites

```bash
# Verify Metatron CLI
metatron smoketest  # Should return "Hello, User: <yourusername>@netflix.com!"
```

```text
A Netflix Gateway Project (NGP) is required for timeline digest generation. If you don’t already have one, you can quickly create a new project here: http://go/modelgateway

Your NGP will be private to you and used exclusively by this tool.
```

---

## 🚀 Quick Start

**Use the service manager:**
```bash
./bin/manage_services.sh start
```

**Then**:
1. Click ⏱️ icon in menu bar → "Start Capture"
2. Open browser → http://localhost:8051
3. View real-time digest and analytics

**Automatic Processing** (defaults - all configurable):
- 📸 Capture: Every 15 minutes (configurable via `capture.fps`)
- 🤖 Annotation: Every 2 minutes (processes in batches of 4 frames)
- 📊 Timeline: Every 5 minutes
- 📋 **Digest: Every 60 minutes** (configurable via `digest.interval_seconds`)

---

## ⚙️ Configuration

**Default Settings** (edit `config/config.yaml` or use Web UI):

```yaml
# Screen capture settings
capture:
  fps: 0.00111111              # 1 frame / 900 sec = every 15 min (default)
  monitor_index: 1             # Which monitor to capture (0 = all monitors)
  retention_days: 1095         # Auto-delete after 3 years
  region: null                 # Capture region [x, y, w, h] or null for full screen

# AI annotation settings
annotation:
  batch_size: 4                # Frames per API call (default: 4 for better context)
  timeout_sec: 30              # API timeout
  api_url: "https://aiopsproxy..."  # Metatron API endpoint
  prompt: "Summarize the type of task..."  # AI instruction

# Timeline settings
timeline:
  bucket_minutes: 30           # Time grouping for continuous activities
  min_tokens_per_bucket: 20    # Filter out minimal activity periods
  output_dir: "./output"       # Where HTML timelines are saved

# Digest settings
digest:
  enabled: true                # Enable automatic digest generation
  interval_seconds: 3600       # Generate every 60 minutes (default: 1 hour)
  ncp_project_id: "prabhuai"   # Your Netflix Gateway Project ID
```

**💡 Tip**: All settings are configurable! Edit the YAML file directly or use the **Settings tab** in the web UI at http://localhost:8051 for a user-friendly interface.

**Common Adjustments**:
- **More frequent captures**: Set `fps: 0.00333333` (every 5 min)
- **Larger batches**: Set `batch_size: 6` (more context for AI)
- **Shorter retention**: Set `retention_days: 30` (save disk space)

---

## 🛠️ Service Management

**Primary Tool**: `bin/manage_services.sh` - Comprehensive service controller

```bash
# Quick Commands
./bin/manage_services.sh start          # Start all services
./bin/manage_services.sh stop           # Stop all services  
./bin/manage_services.sh restart        # Restart all services
./bin/manage_services.sh status         # Check service status

# Individual Services
./bin/manage_services.sh start menubar      # Start only menubar
./bin/manage_services.sh stop webserver     # Stop only webserver
./bin/manage_services.sh restart menubar    # Restart menubar
```

**Individual Scripts** (in `bin/` directory):
- `bin/start_chronometry_agent.sh` / `bin/stop_chronometry_agent.sh`
- `bin/start_chronometry_menubar.sh` / `bin/stop_chronometry_menubar.sh`
- `bin/start_chronometry_webserver.sh` / `bin/stop_chronometry_webserver.sh`

**See [bin/README.md](bin/README.md) for complete script reference**

---

## 📊 How It Works

### Process Flow

```
1. CAPTURE (continuous - default: every 15 min)
   └─→ Screenshots saved to data/frames/YYYY-MM-DD/*.png

2. ANNOTATION (every 2 min - batch_size: 4)
   └─→ AI summaries via Metatron API → *.json files
   └─→ Same summary saved to all frames in batch

3. TIMELINE (every 5 min)
   └─→ Deduplicates batch annotations into single entries
   └─→ Renders markdown formatting in summaries
   └─→ HTML timeline generated → output/timeline_*.html

4. DIGEST (default: every 60 min - configurable)
   └─→ AI daily summary via Copilot API → data/digests/*.json
```

### Data Flow

```
Screenshot → AI Summary → Activity Timeline → Daily Digest
   (PNG)        (JSON)         (HTML)           (JSON)
```

---

## 🌐 Web Dashboard Features

### Dashboard Tab
- **Today's Digest**: AI-generated summary of your day
  - Overall summary (3-4 sentences)
  - Category breakdowns (Code, Meetings, Documentation, etc.)
  - Smart insights and patterns
- **Quick Stats**: Days tracked, frames captured, activities, focus score

### Timeline Tab
- **Detailed Activities**: All activities with categories and durations
- **Batch Deduplication**: Groups batch annotations into single entries with all frames
- **Markdown Rendering**: Beautiful formatting for summaries (bold, lists, code blocks)
- **Inline Expansion**: Click to expand details in-place with screenshot grid
- **Date Picker**: Navigate to any captured date
- **Full Timestamps**: Date with time component displayed

### Analytics Tab
- **Focus Trends**: Daily focus percentage over time
- **API Token Usage**: Track Copilot API consumption (NEW!)
- **Category Breakdown**: Pie chart of activity distribution
- **Hourly Heatmap**: When you're most active

### Search Tab
- **Full-Text Search**: Search through all activity summaries
- **Category Filter**: Filter by activity type
- **Date Range**: Search across multiple days

### Settings Tab
- **Containerized UI**: Settings organized by process (NEW!)
- **Capture Settings**: FPS, monitor, retention
- **Annotation Settings**: Batch size
- **Timeline Settings**: Bucket minutes
- **Digest Settings**: Enable/disable, interval, NCP project ID (NEW!)
- **Live Save**: Updates saved to config.yaml

---

## 📂 Directory Structure

```
Chronometry/
├── bin/                            # Shell scripts (NEW!)
│   ├── manage_services.sh          # Primary service manager
│   ├── start_chronometry_*.sh      # Start scripts (3)
│   └── stop_chronometry_*.sh       # Stop scripts (3)
│
├── config/                         # Configuration files
│   ├── config.yaml                 # Main configuration
│   ├── user.chronometry.menubar.plist
│   ├── user.chronometry.webserver.plist
│   └── README.md                   # Config documentation
│
├── src/                            # Python modules
│   ├── capture.py                  # Screen capture + camera detection
│   ├── annotate.py                 # AI annotation module
│   ├── timeline.py                 # Timeline generation
│   ├── digest.py                   # AI digest generation
│   ├── token_usage.py              # Token usage tracking
│   ├── web_server.py               # Web dashboard server
│   ├── menubar_app.py              # macOS menu bar app
│   ├── common.py                   # Shared utilities
│   ├── quick_test.py               # Testing utilities
│   └── __init__.py                 # Package marker
│
├── templates/
│   └── dashboard.html              # Web dashboard UI
│
├── tests/                          # Unit tests
│   └── test_*.py
│
├── data/                           # Auto-created
│   ├── frames/
│   │   └── YYYY-MM-DD/
│   │       ├── YYYYMMDD_HHMMSS.png
│   │       └── YYYYMMDD_HHMMSS.json (can be synthetic)
│   ├── digests/                    # AI summaries
│   │   └── digest_YYYY-MM-DD.json
│   └── token_usage/                # API token tracking (NEW!)
│       └── YYYY-MM-DD.json
│
├── output/                         # Auto-created
│   └── timeline_YYYY-MM-DD.html
│
├── logs/                           # Service logs
│   ├── menubar.log
│   ├── menubar.error.log
│   ├── webserver.log
│   └── webserver.error.log
│
├── README.md                       # This file
├── SCRIPTS.md                      # Script reference
├── SERVICE_SETUP.md                # Service setup guide
├── requirements.txt                # Dependencies
└── requirements-dev.txt            # Dev dependencies
```

**Structure Benefits:**
- 📁 Clean root directory (only docs and requirements)
- 🔧 All scripts organized in `bin/`
- ⚙️ All config files in `config/`
- 🐍 All Python modules in `src/`
- 📊 Data and output directories auto-created

---

## 🎨 Web Dashboard Preview

### Dashboard Tab - Today's Digest
```
┌────────────────────────────────────────────┐
│ 📋 Today's Digest                          │
├────────────────────────────────────────────┤
│                                            │
│ Summary:                                   │
│ Today's work demonstrated high focus with  │
│ 100% concentration on coding tasks...      │
│                                            │
│ Activity Breakdown:                        │
│ ┌──────────────────────────────────────┐   │
│ │ 💻 Code (9 activities, 25m)          │   │
│ │ Focused on testing Chronometry...    │   │
│ └──────────────────────────────────────┘   │
│                                            │
│ ┌──────────────────────────────────────┐   │
│ │ ⚙️ Work (4 activities, 5m)           │   │
│ │ Slack communications and updates...  │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

The web server provides a full REST API:

### Data Endpoints
```
GET  /api/stats                    # Overall statistics
GET  /api/timeline/<date>          # Activities for date
GET  /api/digest                   # Today's digest (NEW!)
GET  /api/digest/<date>            # Digest for date (NEW!)
GET  /api/analytics?days=7         # Analytics data
GET  /api/search?q=<query>         # Search activities
GET  /api/frames?date=<date>       # List frames
GET  /api/dates                    # Available dates
```

### Configuration Endpoints
```
GET  /api/config                   # Get configuration
PUT  /api/config                   # Update configuration
GET  /api/health                   # Health check
```

### Export Endpoints
```
GET  /api/export/csv?date=<date>   # Export as CSV
GET  /api/export/json?date=<date>  # Export as JSON
```

---

## 🎯 Use Cases

### Daily Work Tracking
- Automatically captures what you're working on
- Generates professional summaries for standups
- Identifies productivity patterns

### Time Management
- See where your time actually goes
- Identify distractions and focus periods
- Optimize your daily schedule

### Project Documentation
- Automatic activity log for projects
- Export timeline for status reports
- Search historical activities

### Team Updates
- Generate professional summaries for team
- Export data for reports
- Track focus time vs meetings

---

## 🛡️ Privacy & Security

### What Data is Collected
- ✅ Screenshots of your active monitor (when camera is off)
- ✅ AI-generated activity summaries
- ✅ Synthetic annotations (when camera is on - no screenshots)
- ✅ Timestamps and metadata
- ✅ API token usage statistics

### Where Data Goes
- ✅ Stored locally in `data/` directory
- ✅ Metatron API: Screenshot summaries (HTTPS, authenticated)
- ✅ Copilot API: Digest generation (HTTPS, authenticated)
- ❌ No external databases
- ❌ No cloud storage
- ❌ No third-party analytics

### How Data is Protected
- 🔒 Local-only storage
- 🔒 HTTPS for all API calls
- 🔒 Automatic cleanup after retention period
- 🔒 Screen lock detection (auto-skip)
- 📹 **Camera detection** - Auto-pauses during video calls (NEW!)
- 🎯 **Synthetic annotations** - Tracks time without screenshots
- 🔒 Path validation prevents data leakage
- 🔒 Input sanitization prevents injection attacks

### Camera Privacy Protection (NEW!)

**Automatic Detection:**
- Detects camera usage via macOS system logs (`com.apple.cmio`)
- Checks hardware registry (`ioreg AppleCameraInterface`)
- Monitors camera LED indicator state
- Works with: Google Meet, Zoom, FaceTime, Teams, Webex

**What Happens:**
1. Camera LED turns ON → Detection triggers
2. Screenshot capture paused automatically
3. Notification: "📹 Camera active - capture skipped"
4. Synthetic annotation created: "In video meeting - screenshot skipped for privacy"
5. Meeting time tracked in timeline/digest
6. Camera OFF → Captures resume automatically

**Privacy Benefits:**
- ✅ No screenshots during video calls
- ✅ No sensitive meeting content captured
- ✅ Timeline remains complete with meeting periods
- ✅ Fully automatic - no manual intervention

---

## 📚 Documentation

- **[README.md](README.md)** - This file - project overview and quick start
- **[bin/README.md](bin/README.md)** - Complete shell script reference (all 7 scripts)
- **[config/README.md](config/README.md)** - Configuration guide
- **Script Headers** - Each .sh file has 50+ line documentation header
- **Code Comments** - Inline documentation in all Python modules

---

## 🐛 Troubleshooting

### "metatron: command not found"
```bash
which metatron  # Check if installed
# Install following Netflix internal documentation
```

### "Port 8051 already in use"
```bash
sudo lsof -i :8051                      # Find process
kill -9 $(lsof -t -i :8051)             # Kill process
./bin/start_chronometry_webserver.sh    # Restart
```

### "No digest generated"
```bash
# Check if enabled
grep "enabled:" config/config.yaml

# Check if annotations exist
ls data/frames/$(date +%Y-%m-%d)/*.json

# Generate manually
python src/digest.py
```

### Web Dashboard Not Updating
```bash
# Hard refresh browser
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)

# Restart web server
./bin/manage_services.sh restart webserver
```

---

## 🔄 Typical Workflow

### Setup (Once)
```bash
# Install and start
pip install -r requirements.txt
./bin/manage_services.sh install    # Install as services
./bin/manage_services.sh start      # Start all services

# Setup keyboard shortcut (see SETUP.md)
# Grant accessibility permission for Cmd+Shift+6 hotkey
```

### Daily Use
```bash
# Open dashboard
http://localhost:8051

# Start monitoring
Click menu bar icon → Start Capture

# Capture important moments
Press Cmd+Shift+6 (instant screenshot)

# View digest
Dashboard → Digest tab → Navigate dates

# Search activities
Search tab → enter keywords

# View detailed timeline
Timeline tab → select date
```

### End of Day
```bash
# Review your day
Dashboard → Today's Digest

# Export data
Export button → Download CSV/JSON

# Stop monitoring
Menu bar → Stop Capture
```

---

## 📊 System Requirements

### Platform
- **macOS**: 10.14+ (for menu bar app)
- **Linux**: Any recent distribution (terminal mode)

### Software
- **Python**: 3.8+
- **Metatron CLI**: For AI annotation
- **Modern Browser**: Chrome, Firefox, Safari, Edge

### Network
- Access to Netflix Copilot API (copilotdpjava)
- Access to Netflix Metatron API (aiopsproxy)

---

## 🎯 Configuration Examples

### High-Frequency Capture (Every 5 minutes)
```yaml
capture:
  fps: 0.00333333  # 1/300 = every 300 seconds (5 min)
annotation:
  batch_size: 6    # Process 6 frames together (30 min context)
digest:
  interval_seconds: 1800  # Digest every 30 min
```

### Low-Frequency Capture (Every 30 minutes)
```yaml
capture:
  fps: 0.00055556  # 1/1800 = every 1800 seconds (30 min)
annotation:
  batch_size: 2    # Process 2 frames together (60 min context)
digest:
  interval_seconds: 7200  # Digest every 2 hours
```

### Batch Annotation Benefits
When using `batch_size > 1`, the AI receives multiple screenshots together:

**Advantages**:
- ✅ **Better Context**: AI sees progression of work across multiple frames
- ✅ **Richer Summaries**: More detailed understanding of tasks
- ✅ **Efficient Timeline**: Batches grouped into single entry with all screenshots
- ✅ **Fewer API Calls**: Reduces token usage and costs

**Default**: `batch_size: 4` (optimal balance of context and performance)

### Work Hours Only (Manual Start/Stop)
```yaml
capture:
  fps: 0.00333333  # Every 5 min when running
digest:
  enabled: true
  interval_seconds: 3600  # Digest every hour
```

---

## 💡 Tips & Best Practices

### For Maximum Privacy
1. Enable pause before sensitive work
2. Set shorter retention period (1-2 days)
3. Review captured frames regularly
4. Use screen lock when away

### For Best Results
1. Let it run for full day
2. Review digest at end of day
3. Use timeline for detailed analysis
4. Export data for records

### For Performance
1. Adjust FPS based on work style
2. Set appropriate retention period
3. Monitor disk space usage
4. Run web server only when needed

---

## 🏗️ Architecture

### Process Architecture
```
┌─────────────────────────────────────────┐
│     Main Agent / Menu Bar App           │
│  (Integrated Process)                   │
└────────────┬────────────────────────────┘
             │
             ├─→ capture.py (continuous)
             ├─→ annotate.py (every 2 min)
             ├─→ timeline.py (every 5 min)
             └─→ digest.py (every 60 min)  ← INTEGRATED!
                     ↓
         ┌──────────────────────┐
         │   Data Storage       │
         │  - frames/           │
         │  - digests/          │
         │  - output/           │
         └──────────┬───────────┘
                    ↑
         ┌──────────────────────┐
         │   Web Server         │
         │   Port 8051          │
         └──────────────────────┘
```

### Technology Stack
- **Backend**: Python 3, Flask, Flask-SocketIO
- **Frontend**: Vue.js 3, Chart.js, Socket.IO
- **AI**: Netflix Metatron API, Copilot API (GPT-4o)
- **Storage**: Local file system (PNG, JSON, HTML)
- **UI**: Netflix-inspired design system

---

## 📈 Performance

### Resource Usage
- **CPU**: ~5-10% during capture
- **Memory**: ~100-150MB typical
- **Disk**: ~1-2MB per hour (with retention cleanup)
- **Network**: Only during API calls (~2-3KB per annotation)

### API Costs & Token Tracking
- **Annotation**: 1 call per frame (~12 calls/hour at 5-min intervals)
- **Digest**: ~5 calls per generation (varies by categories)
- **Token Tracking**: All API calls logged to `data/token_usage/` (NEW!)
- **Analytics Dashboard**: View token consumption over time
- **Average**: ~1,500 tokens per digest generation

---

## 🤝 Contributing

Areas for improvement:
- Mobile companion app
- Weekly/monthly digest summaries
- Export to PDF/Markdown
- Email digest delivery
- Custom digest templates
- Multi-user support

---

## 📄 License

For internal Netflix use. Ensure compliance with Netflix tool policies.

---

## 🙏 Acknowledgments

- **Built with**: Python, Flask, Vue.js, Chart.js, Plotly
- **AI Powered by**: Netflix Copilot API (GPT-4o), Metatron API
- **Design Inspired by**: Netflix's design language
- **Made with** ❤️ for productivity and insights

---

**Version**: 1.0.0  
**Updated**: October 2025  
**Status**: ✅ Production Ready

---

## 🚀 Getting Help

- **Script Reference**: See [bin/README.md](bin/README.md) - Complete guide to all 7 scripts
- **Web Dashboard**: Visit http://localhost:8051 and explore the 5 tabs
- **Configuration**: Edit `config/config.yaml` or use Settings tab in web UI
- **Script Headers**: Each .sh file has detailed usage documentation
- **API Reference**: See API Endpoints section above
