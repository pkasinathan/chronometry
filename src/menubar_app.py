"""Chronometry Menu Bar Application."""

import rumps
import threading
import time
import logging
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import webbrowser
from pynput import keyboard

from capture import capture_screen, capture_single_frame, show_notification, is_screen_locked, is_camera_in_use, create_synthetic_annotation
from annotate import annotate_frames
from timeline import generate_timeline
from digest import generate_daily_digest
from common import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChronometryApp(rumps.App):
    """Menu bar application for Chronometry."""
    
    def __init__(self):
        super(ChronometryApp, self).__init__(
            name="Chronometry",
            icon=None,  # We'll use title instead
            quit_button=None  # We'll create custom quit
        )
        
        # Load configuration
        try:
            self.config = load_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            rumps.alert("Configuration Error", f"Failed to load config.yaml: {e}")
            raise
        
        # Application state
        self.is_running = False
        self.is_paused = False
        self.capture_thread = None
        self.annotation_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Statistics
        self.capture_count = 0
        self.skipped_locked = 0
        self.skipped_camera = 0
        self.start_time = None
        self.manual_captures = 0
        
        # Setup menu
        self.setup_menu()
        
        # Set initial title/icon
        self.title = "⏱️"
        
        # Setup global hotkey (Cmd+Shift+6)
        self.setup_hotkey()
        
    def setup_menu(self):
        """Setup the menu bar items."""
        self.menu = [
            rumps.MenuItem("Start Capture", callback=self.start_capture),
            rumps.MenuItem("Pause", callback=self.toggle_pause),
            rumps.MenuItem("📸 Capture Now (⌘⇧6)", callback=self.capture_now),
            None,  # Separator
            rumps.MenuItem("Run Annotation Now", callback=self.run_annotation),
            rumps.MenuItem("Generate Timeline Now", callback=self.run_timeline),
            rumps.MenuItem("Generate Digest Now", callback=self.run_digest),
            None,  # Separator
            rumps.MenuItem("Open Dashboard", callback=self.open_dashboard),
            rumps.MenuItem("Open Timeline (Today)", callback=self.open_timeline),
            rumps.MenuItem("Open Data Folder", callback=self.open_data_folder),
            None,  # Separator
            rumps.MenuItem("Statistics", callback=self.show_stats),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Initial state
        self.menu["Pause"].set_callback(None)  # Disabled initially
        
    def update_menu_state(self):
        """Update menu items based on current state."""
        if self.is_running:
            self.menu["Start Capture"].title = "Stop Capture"
            self.menu["Pause"].set_callback(self.toggle_pause)
            
            if self.is_paused:
                self.menu["Pause"].title = "⏯️ Resume"
                self.title = "⏱️⏸"  # Clock with pause
            else:
                self.menu["Pause"].title = "⏸️ Pause"
                self.title = "⏱️▶️"  # Clock with play
        else:
            self.menu["Start Capture"].title = "Start Capture"
            self.menu["Pause"].title = "Pause"
            self.menu["Pause"].set_callback(None)  # Disabled
            self.title = "⏱️"
    
    def start_capture(self, _):
        """Start or stop capture."""
        if not self.is_running:
            self._start_capture()
        else:
            self._stop_capture()
    
    def _start_capture(self):
        """Start capture process."""
        logger.info("Starting capture from menu bar...")
        
        # Show notification
        show_notification(
            "Chronometry Starting",
            "Screen capture will begin in 5 seconds. Hide any sensitive data.",
            sound=True
        )
        
        # Reset state
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        self.capture_count = 0
        self.skipped_locked = 0
        self.skipped_camera = 0
        self.start_time = datetime.now()
        
        # Start capture thread
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self.capture_thread.start()
        
        # Start annotation/timeline thread
        self.annotation_thread = threading.Thread(
            target=self._annotation_loop,
            daemon=True
        )
        self.annotation_thread.start()
        
        self.update_menu_state()
        logger.info("Capture started")
    
    def _stop_capture(self):
        """Stop capture process."""
        logger.info("Stopping capture from menu bar...")
        
        self.is_running = False
        self.stop_event.set()
        self.pause_event.set()  # Unpause if paused
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        if self.annotation_thread and self.annotation_thread.is_alive():
            self.annotation_thread.join(timeout=5)
        
        # Show notification
        show_notification(
            "Chronometry Stopped",
            f"Screen capture ended. {self.capture_count} frames captured."
        )
        
        self.update_menu_state()
        logger.info("Capture stopped")
    
    def toggle_pause(self, _):
        """Toggle pause state."""
        if not self.is_running:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_event.clear()
            show_notification(
                "Chronometry Paused",
                "Screen capture is paused. Click Resume to continue."
            )
            logger.info("⏸️ Capture paused")
        else:
            self.pause_event.set()
            show_notification(
                "Chronometry Resumed",
                "Screen capture has resumed."
            )
            logger.info("▶️ Capture resumed")
        
        self.update_menu_state()
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        import mss
        from PIL import Image
        from common import get_frame_path, ensure_dir, cleanup_old_data, get_monitor_config
        
        # Wait 5 seconds after notification
        time.sleep(5)
        
        capture_config = self.config['capture']
        root_dir = self.config['root_dir']
        
        fps = capture_config['fps']
        monitor_index = capture_config['monitor_index']
        region = capture_config['region']
        retention_days = capture_config.get('retention_days', 3)
        
        sleep_interval = 1.0 / fps if fps > 0 else 30.0
        
        last_cleanup = 0
        
        with mss.mss() as sct:
            monitors = sct.monitors
            
            try:
                monitor = get_monitor_config(monitors, monitor_index, region)
            except ValueError as e:
                logger.error(f"Configuration error: {e}")
                return
            
            while not self.stop_event.is_set():
                try:
                    # Wait if paused
                    if self.is_paused:
                        time.sleep(1)
                        continue
                    
                    # Cleanup old data periodically
                    current_time = time.time()
                    if current_time - last_cleanup >= 3600:
                        try:
                            cleanup_old_data(root_dir, retention_days)
                            last_cleanup = current_time
                        except Exception as cleanup_error:
                            logger.warning(f"Cleanup failed: {cleanup_error}")
                    
                    # Check if screen is locked
                    if is_screen_locked():
                        logger.info("🔒 Screen is locked - skipping capture")
                        show_notification("Chronometry", "🔒 Screen locked - capture skipped")
                        self.skipped_locked += 1
                        time.sleep(sleep_interval)
                        continue
                    
                    # Check if camera is in use (video calls, etc.)
                    if is_camera_in_use():
                        logger.info("📹 Camera is in use - skipping capture for privacy")
                        show_notification("Chronometry", "📹 Camera active - capture skipped")
                        
                        # Create synthetic annotation to track the meeting time
                        timestamp = datetime.now()
                        create_synthetic_annotation(
                            root_dir=root_dir,
                            timestamp=timestamp,
                            reason="camera_active",
                            summary="In a video meeting or call - screenshot skipped for privacy"
                        )
                        
                        self.skipped_camera += 1
                        time.sleep(sleep_interval)
                        continue
                    
                    # Show notification before capture
                    show_notification("Chronometry", "📸 Capturing screenshot now...")
                    
                    # Capture screenshot
                    timestamp = datetime.now()
                    frame_path = get_frame_path(root_dir, timestamp)
                    
                    ensure_dir(frame_path.parent)
                    
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    img.save(str(frame_path), "PNG")
                    
                    logger.info(f"Captured: {frame_path.name}")
                    self.capture_count += 1
                    
                except Exception as e:
                    logger.error(f"Error in capture loop: {e}")
                
                time.sleep(sleep_interval)
    
    def _annotation_loop(self):
        """Periodic annotation, timeline generation, and digest creation."""
        # Calculate annotation interval based on capture rate and batch size
        # If batch_size=3 and capture every 5min, wait 15min for 3 frames
        capture_fps = self.config['capture'].get('fps', 0.00333333)
        capture_interval = 1.0 / capture_fps if capture_fps > 0 else 300
        batch_size = self.config['annotation'].get('batch_size', 1)
        
        # Annotation should run after batch_size * capture_interval
        # Add small buffer to ensure frames are ready
        annotation_interval = (batch_size * capture_interval) + 30  
        
        timeline_interval = 300  # 5 minutes
        
        # Get digest interval from config
        digest_config = self.config.get('digest', {})
        digest_interval = digest_config.get('interval_seconds', 3600)  # Default: 1 hour
        digest_enabled = digest_config.get('enabled', True)
        
        last_annotation = 0
        last_timeline = 0
        last_digest = 0
        
        logger.info(f"Annotation will run every {int(annotation_interval)}s (batch_size={batch_size}, capture={int(capture_interval)}s)")
        
        while not self.stop_event.is_set():
            time.sleep(10)  # Check every 10 seconds
            
            if self.is_paused:
                continue
            
            current_time = time.time()
            
            # Run annotation based on calculated interval
            if current_time - last_annotation >= annotation_interval:
                try:
                    logger.info(f"Running periodic annotation (batch_size={batch_size})...")
                    annotate_frames(self.config)
                    last_annotation = current_time
                    logger.info("Annotation completed")
                except Exception as e:
                    logger.error(f"Annotation failed: {e}")
            
            # Run timeline every 5 minutes
            if current_time - last_timeline >= timeline_interval:
                try:
                    logger.info("Generating periodic timeline...")
                    generate_timeline(self.config)
                    last_timeline = current_time
                    logger.info("Timeline generated")
                except Exception as e:
                    logger.error(f"Timeline generation failed: {e}")
            
            # Run digest at configured interval (default: every hour)
            if digest_enabled and current_time - last_digest >= digest_interval:
                try:
                    logger.info("Generating periodic digest...")
                    today = datetime.now()
                    digest = generate_daily_digest(today, self.config)
                    last_digest = current_time
                    if 'error' not in digest:
                        logger.info(f"✓ Digest generated: {digest['total_activities']} activities")
                    else:
                        logger.warning(f"Digest generation returned error: {digest['error']}")
                except Exception as e:
                    logger.error(f"Digest generation failed: {e}")
    
    def capture_now(self, _=None):
        """Manually capture a screenshot immediately.
        
        Can be called from menu item or hotkey (pass _ for menu callback).
        """
        logger.info("Manual capture triggered...")
        
        def run():
            try:
                success = capture_single_frame(self.config, show_notifications=True)
                if success:
                    self.manual_captures += 1
                    logger.info(f"Manual capture successful (total: {self.manual_captures})")
                else:
                    logger.warning("Manual capture was skipped (screen locked or camera active)")
            except Exception as e:
                logger.error(f"Manual capture failed: {e}")
                rumps.notification(
                    "Chronometry",
                    "Capture Failed",
                    f"Error: {str(e)}"
                )
        
        # Run in background thread to not block UI
        threading.Thread(target=run, daemon=True).start()
    
    def run_annotation(self, _):
        """Manually trigger annotation."""
        logger.info("Manual annotation triggered...")
        rumps.notification(
            "Chronometry",
            "Running Annotation",
            "Processing captured frames..."
        )
        
        def run():
            try:
                annotate_frames(self.config)
                rumps.notification(
                    "Chronometry",
                    "Annotation Complete",
                    "Frames have been annotated successfully."
                )
            except Exception as e:
                logger.error(f"Annotation failed: {e}")
                rumps.alert("Annotation Error", str(e))
        
        threading.Thread(target=run, daemon=True).start()
    
    def run_timeline(self, _):
        """Manually trigger timeline generation."""
        logger.info("Manual timeline generation triggered...")
        rumps.notification(
            "Chronometry",
            "Generating Timeline",
            "Creating timeline visualization..."
        )
        
        def run():
            try:
                generate_timeline(self.config)
                rumps.notification(
                    "Chronometry",
                    "Timeline Generated",
                    "Timeline is ready to view."
                )
            except Exception as e:
                logger.error(f"Timeline generation failed: {e}")
                rumps.alert("Timeline Error", str(e))
        
        threading.Thread(target=run, daemon=True).start()
    
    def run_digest(self, _):
        """Manually trigger digest generation."""
        logger.info("Manual digest generation triggered...")
        rumps.notification(
            "Chronometry",
            "Generating Digest",
            "Creating AI-powered daily summary..."
        )
        
        def run():
            try:
                today = datetime.now()
                digest = generate_daily_digest(today, self.config)
                if 'error' not in digest:
                    rumps.notification(
                        "Chronometry",
                        "Digest Generated",
                        f"Daily summary created: {digest['total_activities']} activities"
                    )
                else:
                    rumps.alert("Digest Error", digest['error'])
            except Exception as e:
                logger.error(f"Digest generation failed: {e}")
                rumps.alert("Digest Error", str(e))
        
        threading.Thread(target=run, daemon=True).start()
    
    def open_dashboard(self, _):
        """Open web dashboard in browser."""
        webbrowser.open("http://localhost:8051")
        logger.info("Opened web dashboard")
    
    def open_timeline(self, _):
        """Open today's timeline in browser."""
        output_dir = Path(self.config['timeline'].get('output_dir', './output'))
        today = datetime.now().strftime('%Y-%m-%d')
        timeline_file = output_dir / f"timeline_{today}.html"
        
        if timeline_file.exists():
            webbrowser.open(f"file://{timeline_file.absolute()}")
            logger.info(f"Opened timeline: {timeline_file}")
        else:
            rumps.alert(
                "Timeline Not Found",
                f"No timeline found for today.\nFile: {timeline_file}\n\nGenerate one first."
            )
    
    def open_data_folder(self, _):
        """Open the data folder in Finder."""
        data_dir = Path(self.config['root_dir'])
        subprocess.run(['open', str(data_dir)])
        logger.info(f"Opened data folder: {data_dir}")
    
    def show_stats(self, _):
        """Show statistics."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = "N/A"
        
        status = "Running" if self.is_running else "Stopped"
        if self.is_running and self.is_paused:
            status = "Paused"
        
        message = (
            f"Status: {status}\n"
            f"Uptime: {duration_str}\n"
            f"Frames Captured: {self.capture_count}\n"
            f"Manual Captures: {self.manual_captures}\n"
            f"Skipped (Locked): {self.skipped_locked}\n"
            f"Skipped (Camera): {self.skipped_camera}\n"
        )
        
        rumps.alert("Chronometry Statistics", message)
    
    def setup_hotkey(self):
        """Setup global hotkey listener for Cmd+Shift+6."""
        def on_activate():
            """Callback when hotkey is pressed."""
            logger.info("Hotkey Cmd+Shift+6 pressed - triggering capture")
            self.capture_now()
        
        # Define the hotkey combination: Cmd+Shift+6
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<cmd>+<shift>+6'),
            on_activate
        )
        
        def for_canonical(f):
            """Helper to convert key to canonical form."""
            return lambda k: f(keyboard_listener.canonical(k))
        
        # Create keyboard listener
        keyboard_listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        
        # Start listener in daemon thread
        keyboard_listener.start()
        logger.info("Global hotkey registered: Cmd+Shift+6 for Capture Now")
    
    def quit_app(self, _):
        """Quit the application - stop the service."""
        logger.info("Quit clicked - stopping service")
        
        # Stop capture if running
        if self.is_running:
            try:
                self._stop_capture()
            except:
                pass
        
        # Stop the service (same command as manage_services.sh stop)
        subprocess.run(['launchctl', 'stop', 'com.chronometry.menubar'])
        logger.info("Service stopped")
        
        # Exit
        sys.exit(0)


def main():
    """Main entry point."""
    try:
        app = ChronometryApp()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error in menu bar app: {e}", exc_info=True)
        rumps.alert("Fatal Error", str(e))
        raise


if __name__ == "__main__":
    main()
