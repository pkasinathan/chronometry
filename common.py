"""Common utilities for Chronometry."""

import os
import yaml
import logging
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


def load_config(config_path: str = "config.yaml") -> dict:
    """Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    config_file = Path(config_path)
    
    # Check file exists
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please ensure config.yaml exists in the current directory."
        )
    
    # Load YAML
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in config file: {e}")
    
    # Validate config is a dictionary
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")
    
    # Validate required sections
    required_sections = ['root_dir', 'capture', 'annotation', 'timeline']
    missing = [s for s in required_sections if s not in config]
    if missing:
        raise ValueError(
            f"Missing required configuration sections: {', '.join(missing)}"
        )
    
    # Validate capture settings
    if not isinstance(config['capture'], dict):
        raise ValueError("'capture' section must be a dictionary")
    
    fps = config['capture'].get('fps', 0)
    if not isinstance(fps, (int, float)) or fps < 0:
        raise ValueError("capture.fps must be a non-negative number")
    
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
    
    timeout_sec = config['annotation'].get('timeout_sec', 30)
    if not isinstance(timeout_sec, (int, float)) or timeout_sec <= 0:
        raise ValueError("annotation.timeout_sec must be a positive number")
    
    # Validate timeline settings
    if not isinstance(config['timeline'], dict):
        raise ValueError("'timeline' section must be a dictionary")
    
    bucket_minutes = config['timeline'].get('bucket_minutes', 15)
    if not isinstance(bucket_minutes, int) or bucket_minutes < 1:
        raise ValueError("timeline.bucket_minutes must be a positive integer")
    
    min_tokens = config['timeline'].get('min_tokens_per_bucket', 0)
    if not isinstance(min_tokens, int) or min_tokens < 0:
        raise ValueError("timeline.min_tokens_per_bucket must be a non-negative integer")
    
    logger.info(f"Configuration loaded and validated successfully from {config_path}")
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
    
    frames_dir = root_path / "frames"
    if not frames_dir.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for date_dir in frames_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        try:
            # Parse date from directory name (must be YYYY-MM-DD format)
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
            if dir_date < cutoff_date:
                logger.info(f"Deleting old data: {date_dir}")
                shutil.rmtree(date_dir)
        except ValueError:
            # Skip directories that don't match date format
            logger.debug(f"Skipping non-date directory: {date_dir.name}")
            continue
        except Exception as e:
            logger.error(f"Error deleting {date_dir}: {e}")
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
