"""Common utilities for Chronometry."""

import os
import yaml
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Notification message constants
class NotificationMessages:
    """Centralized notification messages for consistency.
    
    Usage examples:
        show_notification("Title", NotificationMessages.STARTUP)
        show_notification("Title", NotificationMessages.PRE_CAPTURE.format(seconds=5))
        show_notification("Title", NotificationMessages.SCREENSHOT_SAVED.format(filename="test.png"))
    """
    # Startup and status messages
    STARTUP = "Screen capture will begin in 5 seconds. Hide any sensitive data."
    STOPPED = "Screen capture stopped"
    STOPPED_WITH_COUNT = "Screen capture ended. {count} frames captured."
    ERROR_STOPPED = "Screen capture stopped due to an error."
    PAUSED = "Screen capture is paused. Click Resume to continue."
    RESUMED = "Screen capture has resumed."
    
    # Pre-capture warnings
    PRE_CAPTURE = "📸 Capturing in {seconds} seconds - Hide sensitive data now!"
    
    # Skip conditions
    SCREEN_LOCKED = "🔒 Screen locked - capture skipped"
    CAMERA_ACTIVE = "📹 Camera active - capture skipped"
    
    # Success messages
    SCREENSHOT_SAVED = "✅ Screenshot saved: {filename}"
    REGION_SAVED = "✅ Region screenshot saved: {filename}"
    
    # Region capture messages
    SELECT_REGION = "📸 Select region to capture (Esc to cancel)"
    REGION_CANCELLED = "❌ Region capture cancelled"
    REGION_TIMEOUT = "⏱️ Region capture timed out"
    
    # Error messages
    CAPTURE_FAILED = "❌ Capture failed: {error}"
    ANNOTATION_ERROR = "❌ Annotation Error: {error}"
    TIMELINE_ERROR = "❌ Timeline Error: {error}"
    DIGEST_ERROR = "❌ Digest Error: {error}"


def show_notification(title: str, message: str, sound: bool = False):
    """Show macOS notification using osascript.
    
    Args:
        title: Notification title
        message: Notification message
        sound: Whether to play notification sound
    """
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


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.
    
    Args:
        base: Base dictionary (system config)
        override: Override dictionary (user config)
        
    Returns:
        Merged dictionary where override values take precedence
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge(result[key], value)
        else:
            # Override with new value
            result[key] = value
    
    return result


def load_config(config_path: str = "config/config.yaml",
                user_config_path: str = "config/user_config.yaml",
                system_config_path: str = "config/system_config.yaml") -> dict:
    """Load and validate configuration from YAML files.
    
    Supports two modes:
    1. Split mode: Loads user_config.yaml + system_config.yaml and merges them
    2. Legacy mode: Falls back to single config.yaml if split files don't exist
    
    Args:
        config_path: Path to legacy single config file (backward compatibility)
        user_config_path: Path to user config file
        system_config_path: Path to system config file
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        FileNotFoundError: If no config files found
        ValueError: If configuration is invalid
    """
    user_config_file = Path(user_config_path)
    system_config_file = Path(system_config_path)
    legacy_config_file = Path(config_path)
    
    # Try loading split config files first (new method)
    if user_config_file.exists() and system_config_file.exists():
        logger.info("Loading split configuration (user + system)")
        
        try:
            # Load system config (base)
            with open(system_config_file, 'r') as f:
                system_config = yaml.safe_load(f)
            
            # Load user config (overrides)
            with open(user_config_file, 'r') as f:
                user_config = yaml.safe_load(f)
            
            # Merge configs (user overrides system)
            config = deep_merge(system_config, user_config)
            
            # Extract root_dir from paths if in system config
            if 'paths' in config and 'root_dir' in config['paths']:
                config['root_dir'] = config['paths']['root_dir']
            
            # Similarly for output_dir in timeline
            if 'paths' in config and 'output_dir' in config['paths']:
                if 'timeline' not in config:
                    config['timeline'] = {}
                config['timeline']['output_dir'] = config['paths']['output_dir']
            
            logger.info("Split configuration loaded successfully")
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in split config files: {e}")
    
    # Fall back to legacy single config file
    elif legacy_config_file.exists():
        logger.warning(
            f"Using legacy config file: {config_path}. "
            "Consider migrating to user_config.yaml + system_config.yaml using bin/migrate_config.py"
        )
        
        try:
            with open(legacy_config_file, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in config file: {e}")
    
    else:
        # No config files found
        raise FileNotFoundError(
            f"No configuration files found!\n"
            f"Looked for:\n"
            f"  - {user_config_path} + {system_config_path} (split mode)\n"
            f"  - {config_path} (legacy mode)\n"
            f"Please create configuration files or run bin/migrate_config.py"
        )
    
    # Validate config is a dictionary
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")
    
    # Validate required sections
    required_sections = ['capture', 'annotation', 'timeline']
    missing = [s for s in required_sections if s not in config]
    if missing:
        raise ValueError(
            f"Missing required configuration sections: {', '.join(missing)}"
        )
    
    # Ensure root_dir exists (required)
    if 'root_dir' not in config:
        raise ValueError("root_dir is required in configuration")
    
    # Validate capture settings
    if not isinstance(config['capture'], dict):
        raise ValueError("'capture' section must be a dictionary")
    
    # Validate capture_interval_seconds (new) or fps (legacy)
    capture_interval = config['capture'].get('capture_interval_seconds')
    if capture_interval is not None:
        if not isinstance(capture_interval, (int, float)) or capture_interval <= 0:
            raise ValueError("capture.capture_interval_seconds must be a positive number")
    
    retention_days = config['capture'].get('retention_days', 0)
    if not isinstance(retention_days, int) or retention_days < 0:
        raise ValueError("capture.retention_days must be a non-negative integer")
    
    monitor_index = config['capture'].get('monitor_index', 0)
    if not isinstance(monitor_index, int) or monitor_index < 0:
        raise ValueError("capture.monitor_index must be a non-negative integer")
    
    # Validate annotation settings
    if not isinstance(config['annotation'], dict):
        raise ValueError("'annotation' section must be a dictionary")
    
    batch_size = config['annotation'].get('batch_size', 1)
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("annotation.batch_size must be a positive integer")
    
    # Validate timeline settings
    if not isinstance(config['timeline'], dict):
        raise ValueError("'timeline' section must be a dictionary")
    
    bucket_minutes = config['timeline'].get('bucket_minutes', 15)
    if not isinstance(bucket_minutes, int) or bucket_minutes < 1:
        raise ValueError("timeline.bucket_minutes must be a positive integer")
    
    logger.info("Configuration loaded and validated successfully")
    return config


def get_daily_dir(root_dir: str, date: datetime = None) -> Path:
    """Get the directory path for a specific date."""
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    daily_dir = Path(root_dir) / "frames" / date_str
    return daily_dir


def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def cleanup_old_data(root_dir: str, retention_days: int):
    """Delete data older than retention_days with safety checks.
    
    Args:
        root_dir: Root directory for data storage
        retention_days: Number of days to keep data
        
    Cleans up:
    - frames/YYYY-MM-DD/ directories
    - digests/digest_YYYY-MM-DD.json files
    - token_usage/YYYY-MM-DD.json files
    - output/timeline_YYYY-MM-DD.html files
    """
    if retention_days <= 0:
        return
    
    # Validate root_dir is safe
    root_path = Path(root_dir).resolve()
    current_dir = Path.cwd().resolve()
    
    # Ensure root_dir is within current directory tree for safety
    try:
        root_path.relative_to(current_dir)
    except ValueError:
        logger.warning(
            f"Skipping cleanup - root_dir '{root_dir}' is outside current directory. "
            f"This is a safety measure to prevent accidental deletion."
        )
        return
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # Cleanup frames directories
    frames_dir = root_path / "frames"
    if frames_dir.exists():
        for date_dir in frames_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            try:
                # Parse date from directory name (must be YYYY-MM-DD format)
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    logger.info(f"Deleting old frames: {date_dir}")
                    shutil.rmtree(date_dir)
            except ValueError:
                # Skip directories that don't match date format
                logger.debug(f"Skipping non-date directory: {date_dir.name}")
                continue
            except Exception as e:
                logger.error(f"Error deleting {date_dir}: {e}")
                continue
    
    # Cleanup digest files
    digests_dir = root_path / "digests"
    if digests_dir.exists():
        for digest_file in digests_dir.glob("digest_*.json"):
            try:
                # Extract date from filename: digest_YYYY-MM-DD.json
                date_str = digest_file.stem.replace("digest_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    logger.info(f"Deleting old digest: {digest_file}")
                    digest_file.unlink()
            except (ValueError, Exception) as e:
                logger.debug(f"Skipping file {digest_file}: {e}")
                continue
    
    # Cleanup token usage files
    token_dir = root_path / "token_usage"
    if token_dir.exists():
        for token_file in token_dir.glob("*.json"):
            try:
                # Filename format: YYYY-MM-DD.json
                date_str = token_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    logger.info(f"Deleting old token usage: {token_file}")
                    token_file.unlink()
            except (ValueError, Exception) as e:
                logger.debug(f"Skipping file {token_file}: {e}")
                continue
    
    # Cleanup output timeline files (check parent directory for output/)
    output_dir = current_dir / "output"
    if output_dir.exists():
        for timeline_file in output_dir.glob("timeline_*.html"):
            try:
                # Extract date from filename: timeline_YYYY-MM-DD.html
                date_str = timeline_file.stem.replace("timeline_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    logger.info(f"Deleting old timeline: {timeline_file}")
                    timeline_file.unlink()
            except (ValueError, Exception) as e:
                logger.debug(f"Skipping file {timeline_file}: {e}")
                continue


def get_frame_path(root_dir: str, timestamp: datetime) -> Path:
    """Get the full path for a frame file."""
    daily_dir = get_daily_dir(root_dir, timestamp)
    filename = timestamp.strftime("%Y%m%d_%H%M%S.png")
    return daily_dir / filename


def get_json_path(png_path: Path, json_suffix: str = ".json") -> Path:
    """Get the JSON path corresponding to a PNG file."""
    return png_path.with_suffix(json_suffix)


def get_monitor_config(monitors: list, monitor_index: int, region: Optional[list] = None) -> dict:
    """Get monitor configuration for screenshot capture.
    
    Args:
        monitors: List of available monitors from mss
        monitor_index: Index of monitor to capture (0 = all, 1+ = specific)
        region: Optional [x, y, width, height] for custom region
        
    Returns:
        Monitor dictionary compatible with mss.grab()
        
    Raises:
        ValueError: If monitor_index is invalid or region format is wrong
    """
    if monitor_index >= len(monitors):
        raise ValueError(
            f"Monitor index {monitor_index} not found. "
            f"Available monitors: 0-{len(monitors)-1} ({len(monitors)} total)"
        )
    
    if region:
        # Validate region format
        if not isinstance(region, list) or len(region) != 4:
            raise ValueError(
                "Region must be a list of [x, y, width, height]. "
                f"Got: {region}"
            )
        
        # Validate all values are integers
        if not all(isinstance(x, int) for x in region):
            raise ValueError(
                "All region values must be integers. "
                f"Got: {region}"
            )
        
        return {
            "left": region[0],
            "top": region[1],
            "width": region[2],
            "height": region[3]
        }
    else:
        return monitors[monitor_index]


# TODO: Implement optional pause/resume functionality
# def is_paused(pause_file_path: str = None) -> bool:
#     """Check if capture is paused by looking for pause flag file."""
#     pass


# TODO: Implement optional blur/redaction regions
# def apply_redactions(image, redaction_regions: list):
#     """Apply blur/redaction to specified regions."""
#     pass
