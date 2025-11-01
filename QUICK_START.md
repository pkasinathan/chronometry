# ⚡ Chronometry Quick Start

Get up and running in **5 minutes** with this streamlined guide.

---

## 🎯 What is Chronometry?

An AI-powered work activity tracker that:
- 📸 Automatically captures screenshots of your work
- 🤖 Uses AI to summarize what you're doing
- 📊 Creates beautiful timelines and daily digests
- 🔒 Stores everything locally on your Mac

---

## ⚠️ Prerequisites (Critical!)

### 1. **Metatron CLI** (Required)

Verify it's installed:
```bash
metatron smoketest
```

**Expected output**: `Hello, User: <yourusername>@netflix.com!`

**If not installed**: Follow Netflix internal documentation to install Metatron CLI

### 2. **Netflix Gateway Project** (Required for Digest)

You need an NGP (Netflix Gateway Project) for AI digest generation.

**Create one here**: https://genai.netflix.net/projects/edit

- ✅ Create a **new private project** (takes 30 seconds)
- ✅ Name it something like `<yourinitials>chronometry`. 
  - Example: 
    - GenAI Project ID: `pkasichronometry`.
    - GenAI Project Name: `pkasichronometry`
    - Use Case Description(required): `AI project which is used on my Chronometry Application for digest generation.`
    - You can disable Braintrust logging and Notebooks access. Do not grant access to anyone else.
- ✅ It's private to you and used only by your tool

---

## 🚀 Installation (One Command!)

```bash
# Clone the repository
git clone https://github.netflix.net/pkasinathan/chronometry.git
cd chronometry

# Install and start services (auto-creates venv, installs dependencies)
./bin/manage_services.sh install
```

**What this does**:
- ✅ Creates Python virtual environment
- ✅ Installs all dependencies
- ✅ Configures services to run at boot
- ✅ Starts web server and menu bar app

---

## ⚙️ Configure Your NGP Project ID

Before first use, set your Netflix Gateway Project ID:

### Option 1: Web UI (Easiest)
1. Open http://localhost:8051
2. Go to **Settings** tab
3. Find **"NCP Project Name"** field
4. Enter your project ID (e.g., `chronometry-yourname`)
5. Click **"💾 Save Changes"**

### Option 2: Edit Config File
```bash
nano config/user_config.yaml
```

Find and update:
```yaml
digest:
  ncp_project_id: "your-project-id-here"  # Replace with your project ID
```

**Note**: Chronometry now uses split configs:
- `user_config.yaml` - Your customizable settings (edit this!)
- `system_config.yaml` - System settings (advanced only)
- `config.yaml` - Legacy (still supported for backward compatibility)

---

## ✅ Verify Everything Works

### 1. Check Services are Running
```bash
./bin/manage_services.sh status
```

**Expected output**:
```
✓ Web Server: Running
✓ Port 8051: Listening
✓ Menu Bar App: Running
```

### 2. Access the Dashboard
Open your browser: **http://localhost:8051**

You should see:
- 📊 Dashboard tab with stats
- 📅 Timeline tab (will populate as you work)
- ⚙️ Settings tab (configure here)

### 3. Start Capturing
Click the **⏱️ icon** in your Mac menu bar → **"Start Capture"**

---

## 📖 Basic Usage

### Daily Workflow

1. **Morning**: Services auto-start at login (if installed)
2. **Start Capture**: Click menu bar ⏱️ → "Start Capture"
3. **Work Normally**: System captures screenshots every 15 minutes
4. **View Progress**: Open http://localhost:8051 anytime
5. **End of Day**: Review your digest on Dashboard tab

### Menu Bar Controls

Click **⏱️** in menu bar:
- **Start Capture** - Begin monitoring
- **Pause** - Temporarily pause (for sensitive work)
- **Open Dashboard** - Quick access to web UI
- **Quit** - Stop the menu bar app

### Common Commands

```bash
# Start services
./bin/manage_services.sh start

# Stop services
./bin/manage_services.sh stop

# Check status
./bin/manage_services.sh status

# View logs
./bin/manage_services.sh logs
```

---

## 🔧 Adjust Capture Frequency (Optional)

By default, captures every **15 minutes**. To change:

1. Open http://localhost:8051 → **Settings** tab
2. Find **"Capture FPS"** field
3. Common values:
   - `0.00333333` = every 5 minutes (high frequency)
   - `0.00111111` = every 15 minutes (default)
   - `0.00055556` = every 30 minutes (low frequency)
4. Click **"💾 Save Changes"**

---

## 🎯 What to Expect

### First Hour
- ✅ Screenshots captured automatically
- ✅ AI summaries generated every 2 minutes
- ✅ Timeline updates every 5 minutes
- ✅ First digest generated after 60 minutes

### Timeline Tab
- **Collapsed view**: Shows activity with markdown-formatted summary
- **Click to expand**: See all screenshots from that time period
- **Navigate dates**: Use date picker to view previous days

### Dashboard Tab
- **Today's Digest**: AI-generated summary of your work
- **Category Breakdown**: Code, Meetings, Documentation, etc.
- **Quick Stats**: Days tracked, frames captured, focus score

---

## 🆘 Troubleshooting

### "No activities recorded yet"
- **Cause**: No screenshots captured yet
- **Solution**: Wait 15 minutes for first capture, or use Cmd+Shift+6 for instant capture

### "metatron: command not found"
- **Cause**: Metatron CLI not installed
- **Solution**: Install Metatron following Netflix internal docs

### "Digest generation failed"
- **Cause**: NGP project ID not configured or invalid
- **Solution**: 
  1. Verify you created an NGP at http://go/modelgateway
  2. Update `ncp_project_id` in Settings tab
  3. Click "🔄 Regenerate" on Dashboard

### Port 8051 already in use
```bash
# Find and kill the process
lsof -i :8051
kill -9 <PID>

# Restart service
./bin/manage_services.sh restart
```

### Services won't stop
```bash
# Force uninstall and reinstall
./bin/manage_services.sh uninstall
./bin/manage_services.sh install
```

---

## 🔒 Privacy & Security

- ✅ **All data stored locally** on your Mac in `./data/` directory
- ✅ **No cloud storage** - screenshots never leave your machine except for AI API calls
- ✅ **Camera detection** - Automatically pauses during video calls
- ✅ **Screen lock aware** - Skips captures when screen is locked
- ✅ **Auto-cleanup** - Old data deleted after 3 years (configurable)

---

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **Explore Analytics**: View productivity charts and patterns
2. **Search Activities**: Find specific tasks across days
3. **Export Data**: Download CSV/JSON for records
4. **Customize Settings**: Adjust capture frequency, batch size, etc.
5. **Read Full Documentation**: See [README.md](README.md) for complete details

---

## 📚 Full Documentation

- **[README.md](README.md)** - Complete project documentation
- **[bin/README.md](bin/README.md)** - Advanced script reference
- **[config/README.md](config/README.md)** - Configuration guide

---

## 🚨 Important Notes

1. **Metatron CLI is required** - Install it first!
2. **NGP Project ID must be configured** - Create one at http://go/modelgateway
3. **Services run at boot** - They'll auto-start after installation
4. **First digest takes 60 minutes** - Be patient for initial AI summary
5. **Screenshots are local only** - Your data stays on your Mac

---

## ✨ Quick Reference

| What | Where | How |
|------|-------|-----|
| **Install** | Terminal | `./bin/manage_services.sh install` |
| **Start** | Menu Bar or Terminal | Click ⏱️ → Start OR `./bin/manage_services.sh start` |
| **Dashboard** | Browser | http://localhost:8051 |
| **Settings** | Web UI | http://localhost:8051 → Settings tab |
| **Stop** | Terminal | `./bin/manage_services.sh stop` |
| **Status** | Terminal | `./bin/manage_services.sh status` |

---

**Need Help?** Check the [README.md](README.md) or run `./bin/manage_services.sh` without arguments to see all options.

**Questions?** Contact the Chronometry team or check internal documentation.

---

**Happy Tracking! ⏱️**

