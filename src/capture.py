"""Screen capture module for Chronometry."""

import time
import logging
import subprocess
from datetime import datetime
import mss
from PIL import Image
from common import (
    load_config, ensure_dir, cleanup_old_data, get_frame_path, get_monitor_config
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_notification(title: str, message: str, sound: bool = False):
    """Show macOS notification using osascript."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        if sound:
            script += ' sound name "default"'
        
        subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            timeout=5
        )
        logger.debug(f"Notification shown: {title} - {message}")
    except Exception as e:
        logger.warning(f"Failed to show notification: {e}")


def is_screen_locked() -> bool:
    """Check if the macOS screen is locked."""
    try:
        # Check if screen is locked using Python's Quartz framework
        # First try using ioreg to check screensaver state
        result = subprocess.run(
            ['ioreg', '-n', 'IODisplayWrangler'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        # If IOPowerManagement shows the display is off/sleeping, screen is likely locked
        if 'IOPowerManagement' in result.stdout:
            if '"CurrentPowerState"=0' in result.stdout or '"CurrentPowerState"=1' in result.stdout:
                return True
        
        # Alternative: Check if screensaver is running
        screensaver_check = subprocess.run(
            ['pgrep', '-x', 'ScreenSaverEngine'],
            capture_output=True,
            timeout=2
        )
        
        if screensaver_check.returncode == 0:
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Screen lock detection failed: {e}")
        # If we can't determine, assume screen is unlocked (fail safe for capturing)
        return False


def create_synthetic_annotation(root_dir: str, timestamp: datetime, reason: str, summary: str):
    """Create a synthetic annotation when capture is skipped.
    
    Args:
        root_dir: Root directory for data
        timestamp: Timestamp for the annotation
        reason: Reason for skipping (e.g., 'camera', 'locked')
        summary: Human-readable summary
    """
    from common import get_frame_path, ensure_dir
    from pathlib import Path
    import json
    
    try:
        # Get the path where the screenshot would have been
        frame_path = get_frame_path(root_dir, timestamp)
        ensure_dir(frame_path.parent)
        
        # Create JSON annotation file (without the PNG)
        json_path = frame_path.with_suffix('.json')
        
        annotation = {
            "timestamp": timestamp.isoformat(),
            "summary": summary,
            "image_file": None,  # No screenshot taken
            "synthetic": True,
            "reason": reason
        }
        
        with open(json_path, 'w') as f:
            json.dump(annotation, f, indent=2)
        
        logger.info(f"Synthetic annotation created: {summary}")
    except Exception as e:
        logger.warning(f"Failed to create synthetic annotation: {e}")


def is_camera_in_use() -> bool:
    """Check if camera is currently in use (video calls, etc.).
    
    Checks macOS Control Center camera indicator (the green icon in menubar).
    """
    try:
        # MOST ACCURATE: Check for camera indicator in Control Center
        # When camera is in use, macOS shows a green camera icon in the menubar
        # This is managed by the Control Center process
        
        # Check system logs for camera streaming
        result = subprocess.run(
            ['log', 'show', '--predicate', 'subsystem == "com.apple.cmio"', '--last', '5s', '--info'],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        # Look for active streaming indicators
        if 'Starting' in result.stdout or 'stream' in result.stdout.lower():
            logger.info("📹 Camera detected in use via system logs")
            return True
        
        # Method 2: Check ioreg for camera interface (works for native apps)
        ioreg_result = subprocess.run(
            ['ioreg', '-r', '-n', 'AppleCameraInterface', '-w', '0'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        # When camera LED is on, IOUserClientCreator will be present
        if 'IOUserClientCreator' in ioreg_result.stdout:
            logger.info("📹 Camera detected in use via ioreg")
            return True
        
        # Method 3: Check for camera framework usage by Chrome
        # If Chrome has CMIO (CoreMediaIO) files open, camera might be active
        lsof_result = subprocess.run(
            ['sh', '-c', 'lsof -c "Google Chrome Helper" 2>/dev/null | grep -c CMIO'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        try:
            cmio_count = int(lsof_result.stdout.strip())
            # If Chrome has multiple CMIO files open (>5), camera is likely active
            if cmio_count > 5:
                logger.info(f"📹 Camera detected in use via Chrome CMIO ({cmio_count} files)")
                return True
        except:
            pass
        
        # Method 4: Check for FaceTime
        facetime_check = subprocess.run(
            ['pgrep', '-x', 'FaceTime'],
            capture_output=True,
            timeout=1
        )
        if facetime_check.returncode == 0:
            logger.info("📹 Camera likely in use via FaceTime")
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Camera detection failed: {e}")
        # If we can't determine, assume camera is NOT in use
        return False


def capture_screen(config: dict):
    """Capture screen based on configuration with error recovery."""
    capture_config = config['capture']
    root_dir = config['root_dir']
    
    # Get capture settings
    fps = capture_config['fps']
    monitor_index = capture_config['monitor_index']
    region = capture_config['region']
    retention_days = capture_config.get('retention_days', 3)
    
    # Calculate sleep interval
    sleep_interval = 1.0 / fps if fps > 0 else 30.0
    
    logger.info("Starting screen capture...")
    logger.info(f"FPS: {fps} (capturing every {sleep_interval:.2f} seconds)")
    logger.info(f"Monitor: {monitor_index}")
    logger.info(f"Region: {region if region else 'Full screen'}")
    logger.info(f"Saving to: {root_dir}/frames/")
    logger.info("Press Ctrl+C to stop")
    
    # Show initial notification warning
    show_notification(
        "Chronometry Starting",
        "Screen capture will begin in 5 seconds. Hide any sensitive data.",
        sound=True
    )
    logger.info("⚠️ Notification shown: Capture starting in 5 seconds...")
    time.sleep(5)
    
    with mss.mss() as sct:
        # Get monitor info
        monitors = sct.monitors
        
        # Set capture region using common function
        try:
            monitor = get_monitor_config(monitors, monitor_index, region)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return
        
        last_cleanup = 0
        error_count = 0
        max_consecutive_errors = 5
        capture_count = 0
        skipped_locked = 0
        
        try:
            while True:
                try:
                    # Cleanup old data periodically (once per hour)
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
                        skipped_locked += 1
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
                        
                        time.sleep(sleep_interval)
                        continue
                    
                    # Show notification before capture
                    show_notification("Chronometry", "📸 Capturing screenshot now...")
                    
                    # Capture screenshot
                    timestamp = datetime.now()
                    frame_path = get_frame_path(root_dir, timestamp)
                    
                    # Ensure directory exists
                    ensure_dir(frame_path.parent)
                    
                    # Take screenshot
                    screenshot = sct.grab(monitor)
                    
                    # Convert to PIL Image and save
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    img.save(str(frame_path), "PNG")
                    
                    logger.info(f"Captured: {frame_path.name}")
                    capture_count += 1
                    
                    # Reset error count on successful capture
                    error_count = 0
                    
                except KeyboardInterrupt:
                    # Re-raise to be caught by outer handler
                    raise
                    
                except Exception as capture_error:
                    # Log error but continue capturing
                    error_count += 1
                    logger.error(f"Error capturing frame (error {error_count}): {capture_error}")
                    
                    # If too many consecutive errors, exit
                    if error_count >= max_consecutive_errors:
                        logger.critical(
                            f"Too many consecutive errors ({error_count}). "
                            "Stopping capture process."
                        )
                        break
                    
                    logger.info("Continuing capture loop...")
                
                # Sleep until next capture
                time.sleep(sleep_interval)
                
        except KeyboardInterrupt:
            logger.info("\nCapture stopped by user")
            show_notification(
                "MyWorkAnalyzer Stopped",
                f"Screen capture ended. {capture_count} frames captured."
            )
        except Exception as e:
            logger.error(f"Fatal error during capture: {e}", exc_info=True)
            show_notification(
                "MyWorkAnalyzer Error",
                "Screen capture stopped due to an error."
            )


def main():
    """Main entry point."""
    try:
        config = load_config()
        
        # Start capturing
        capture_screen(config)
        
    except Exception as e:
        logger.error(f"Fatal error in capture process: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
