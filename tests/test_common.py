"""Tests for common.py utilities."""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import (
    load_config, get_daily_dir, ensure_dir, get_frame_path, 
    get_json_path, get_monitor_config, cleanup_old_data
)


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_config_valid(self):
        """Test loading a valid configuration file."""
        config = load_config("tests/fixtures/config_test.yaml")
        assert 'root_dir' in config
        assert 'capture' in config
        assert 'annotation' in config
        assert 'timeline' in config
    
    def test_load_config_missing_file(self):
        """Test error handling for missing config."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config("nonexistent.yaml")
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test error handling for invalid YAML."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "yaml" in str(exc_info.value).lower()
    
    def test_load_config_missing_sections(self, tmp_path):
        """Test validation of required sections."""
        config_file = tmp_path / "incomplete_config.yaml"
        config_file.write_text("root_dir: ./data\n")
        
        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "missing" in str(exc_info.value).lower()
    
    def test_load_config_invalid_fps(self, tmp_path):
        """Test validation of FPS value."""
        config_file = tmp_path / "bad_fps.yaml"
        config_data = {
            'root_dir': './data',
            'capture': {'fps': -1},
            'annotation': {'batch_size': 1, 'timeout_sec': 30},
            'timeline': {'bucket_minutes': 15, 'min_tokens_per_bucket': 0}
        }
        config_file.write_text(yaml.dump(config_data))
        
        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "fps" in str(exc_info.value).lower()


class TestGetDailyDir:
    """Tests for get_daily_dir function."""
    
    def test_get_daily_dir_with_date(self):
        """Test daily directory path generation with specific date."""
        date = datetime(2025, 10, 4)
        result = get_daily_dir("./data", date)
        assert str(result).endswith("2025-10-04")
        assert "data/frames" in str(result)
    
    def test_get_daily_dir_without_date(self):
        """Test daily directory path generation with current date."""
        result = get_daily_dir("./data")
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in str(result)
        assert "data/frames" in str(result)


class TestGetFramePath:
    """Tests for get_frame_path function."""
    
    def test_get_frame_path(self):
        """Test frame file path generation."""
        timestamp = datetime(2025, 10, 4, 14, 30, 45)
        result = get_frame_path("./data", timestamp)
        assert result.name == "20251004_143045.png"
        assert "2025-10-04" in str(result)


class TestGetJsonPath:
    """Tests for get_json_path function."""
    
    def test_get_json_path_default_suffix(self):
        """Test JSON path generation from PNG path."""
        png_path = Path("data/frames/2025-10-04/20251004_143045.png")
        json_path = get_json_path(png_path)
        assert json_path.suffix == ".json"
        assert json_path.stem == png_path.stem
    
    def test_get_json_path_custom_suffix(self):
        """Test JSON path generation with custom suffix."""
        png_path = Path("data/frames/2025-10-04/20251004_143045.png")
        json_path = get_json_path(png_path, ".annotation")
        assert json_path.suffix == ".annotation"


class TestEnsureDir:
    """Tests for ensure_dir function."""
    
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test" / "nested" / "dir"
        ensure_dir(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_ensure_dir_existing_directory(self, tmp_path):
        """Test with existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        ensure_dir(test_dir)  # Should not raise error
        assert test_dir.exists()


class TestGetMonitorConfig:
    """Tests for get_monitor_config function."""
    
    def test_get_monitor_config_no_region(self):
        """Test monitor configuration without custom region."""
        monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            {"left": 1920, "top": 0, "width": 1920, "height": 1080}
        ]
        result = get_monitor_config(monitors, 1)
        assert result == monitors[1]
    
    def test_get_monitor_config_with_region(self):
        """Test monitor configuration with custom region."""
        monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        region = [100, 100, 800, 600]
        result = get_monitor_config(monitors, 0, region)
        
        assert result["left"] == 100
        assert result["top"] == 100
        assert result["width"] == 800
        assert result["height"] == 600
    
    def test_get_monitor_config_invalid_index(self):
        """Test error handling for invalid monitor index."""
        monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        
        with pytest.raises(ValueError) as exc_info:
            get_monitor_config(monitors, 5)
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_monitor_config_invalid_region_format(self):
        """Test error handling for invalid region format."""
        monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        
        with pytest.raises(ValueError):
            get_monitor_config(monitors, 0, [100, 100])  # Wrong length
    
    def test_get_monitor_config_invalid_region_types(self):
        """Test error handling for non-integer region values."""
        monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        
        with pytest.raises(ValueError):
            get_monitor_config(monitors, 0, [100, "200", 800, 600])


class TestCleanupOldData:
    """Tests for cleanup_old_data function."""
    
    def test_cleanup_old_data_zero_retention(self, tmp_path):
        """Test that zero retention days results in no cleanup."""
        cleanup_old_data(str(tmp_path), 0)
        # Should complete without error
    
    def test_cleanup_old_data_no_frames_dir(self, tmp_path):
        """Test with non-existent frames directory."""
        cleanup_old_data(str(tmp_path), 3)
        # Should complete without error
    
    def test_cleanup_old_data_removes_old_dirs(self, tmp_path):
        """Test that old directories are removed."""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create old directory
        old_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        old_dir = frames_dir / old_date
        old_dir.mkdir()
        (old_dir / "test.png").write_text("test")
        
        # Create recent directory
        recent_date = datetime.now().strftime("%Y-%m-%d")
        recent_dir = frames_dir / recent_date
        recent_dir.mkdir()
        (recent_dir / "test.png").write_text("test")
        
        # Run cleanup with 3 day retention
        cleanup_old_data(str(tmp_path), 3)
        
        # Old directory should be removed, recent should remain
        assert not old_dir.exists()
        assert recent_dir.exists()
    
    def test_cleanup_old_data_skips_non_date_dirs(self, tmp_path):
        """Test that non-date directories are not removed."""
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        
        # Create non-date directory
        other_dir = frames_dir / "other_stuff"
        other_dir.mkdir()
        
        cleanup_old_data(str(tmp_path), 3)
        
        # Non-date directory should still exist
        assert other_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

