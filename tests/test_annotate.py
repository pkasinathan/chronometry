"""Tests for annotate.py module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.annotate import (
    encode_image_to_base64,
    call_metatron_api,
    call_metatron_api_with_retry,
    process_batch,
    annotate_frames
)
from datetime import datetime


class TestEncodeImageToBase64:
    """Tests for encode_image_to_base64 function."""
    
    def test_encode_image(self, tmp_path):
        """Test encoding an image file to base64."""
        # Create a simple test file
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image data")
        
        result = encode_image_to_base64(test_file)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Base64 encoding of "fake image data"
        assert result != ""


class TestCallMetatronAPI:
    """Tests for call_metatron_api function."""
    
    def test_call_metatron_api_url_validation(self):
        """Test API URL validation."""
        config = {
            'annotation': {
                'api_url': 'ftp://invalid.com/api',  # Invalid scheme
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            call_metatron_api([], config)
        assert "scheme" in str(exc_info.value).lower()
    
    def test_call_metatron_api_missing_netloc(self):
        """Test API URL validation for missing network location."""
        config = {
            'annotation': {
                'api_url': 'https://',  # Missing netloc
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            call_metatron_api([], config)
        assert "network location" in str(exc_info.value).lower()
    
    @patch('annotate.subprocess.run')
    @patch('annotate.tempfile.NamedTemporaryFile')
    @patch('annotate.os.unlink')
    def test_call_metatron_api_success(self, mock_unlink, mock_temp, mock_run):
        """Test successful API call."""
        # Setup mocks
        mock_temp.return_value.__enter__.return_value.name = '/tmp/test.json'
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"summary": "test summary", "sources": ["test"]}'
        )
        
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test prompt',
                'timeout_sec': 30
            }
        }
        
        images = [{"name": "test", "content_type": "image/png", "base64_data": "abc123"}]
        result = call_metatron_api(images, config)
        
        assert result['summary'] == 'test summary'
        assert result['sources'] == ['test']
    
    @patch('annotate.subprocess.run')
    @patch('annotate.tempfile.NamedTemporaryFile')
    @patch('annotate.os.unlink')
    def test_call_metatron_api_invalid_json_response(self, mock_unlink, mock_temp, mock_run):
        """Test handling of invalid JSON response."""
        mock_temp.return_value.__enter__.return_value.name = '/tmp/test.json'
        mock_run.return_value = Mock(
            returncode=0,
            stdout='invalid json{'
        )
        
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test prompt',
                'timeout_sec': 30
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            call_metatron_api([], config)
        assert "json" in str(exc_info.value).lower()
    
    @patch('annotate.subprocess.run')
    @patch('annotate.tempfile.NamedTemporaryFile')
    @patch('annotate.os.unlink')
    def test_call_metatron_api_command_failure(self, mock_unlink, mock_temp, mock_run):
        """Test handling of command failure."""
        mock_temp.return_value.__enter__.return_value.name = '/tmp/test.json'
        mock_run.return_value = Mock(
            returncode=1,
            stderr='Command failed'
        )
        
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test prompt',
                'timeout_sec': 30
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            call_metatron_api([], config)
        assert "failed" in str(exc_info.value).lower()


class TestRetryLogic:
    """Tests for API retry logic."""
    
    @patch('src.annotate.call_metatron_api')
    @patch('src.annotate.time.sleep')
    def test_retry_succeeds_on_second_attempt(self, mock_sleep, mock_api):
        """Test that retry succeeds on second attempt."""
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        # First call fails, second succeeds
        mock_api.side_effect = [
            Exception("First attempt failed"),
            {'summary': 'success', 'sources': []}
        ]
        
        images = [{"name": "test", "content_type": "image/png", "base64_data": "abc"}]
        result = call_metatron_api_with_retry(images, config)
        
        assert result['summary'] == 'success'
        assert mock_api.call_count == 2
        mock_sleep.assert_called_once_with(1)  # Exponential backoff: 2^0 = 1
    
    @patch('src.annotate.call_metatron_api')
    @patch('src.annotate.time.sleep')
    def test_retry_exponential_backoff(self, mock_sleep, mock_api):
        """Test exponential backoff timing."""
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        # Fail twice, succeed on third
        mock_api.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            {'summary': 'success', 'sources': []}
        ]
        
        images = [{"name": "test", "content_type": "image/png", "base64_data": "abc"}]
        call_metatron_api_with_retry(images, config)
        
        # Verify exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # 2^0 = 1
        mock_sleep.assert_any_call(2)  # 2^1 = 2
    
    @patch('src.annotate.call_metatron_api')
    def test_retry_fails_after_max_attempts(self, mock_api):
        """Test that exception is raised after max retries."""
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        mock_api.side_effect = Exception("API failed")
        
        images = [{"name": "test", "content_type": "image/png", "base64_data": "abc"}]
        
        with pytest.raises(Exception) as exc_info:
            call_metatron_api_with_retry(images, config, max_retries=3)
        
        assert "API failed" in str(exc_info.value)
        assert mock_api.call_count == 3
    
    @patch('src.annotate.call_metatron_api')
    def test_retry_succeeds_immediately(self, mock_api):
        """Test that no retry occurs when first attempt succeeds."""
        config = {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test',
                'timeout_sec': 30
            }
        }
        
        mock_api.return_value = {'summary': 'success', 'sources': []}
        
        images = [{"name": "test", "content_type": "image/png", "base64_data": "abc"}]
        result = call_metatron_api_with_retry(images, config)
        
        assert result['summary'] == 'success'
        assert mock_api.call_count == 1


class TestBatchProcessing:
    """Tests for batch processing."""
    
    @pytest.fixture
    def test_config(self):
        """Provide test configuration."""
        return {
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test prompt',
                'timeout_sec': 30,
                'json_suffix': '.json',
                'batch_size': 4
            }
        }
    
    @patch('src.annotate.save_json')
    @patch('src.annotate.call_metatron_api_with_retry')
    @patch('src.annotate.encode_image_to_base64')
    def test_process_batch_success(self, mock_encode, mock_api, mock_save, test_config, tmp_path):
        """Test successful batch processing."""
        # Create test images
        image_paths = []
        for i in range(3):
            img_path = tmp_path / f"test_{i}.png"
            img_path.write_bytes(b"fake image")
            image_paths.append(img_path)
        
        mock_encode.return_value = "base64data"
        mock_api.return_value = {
            'summary': 'Batch summary',
            'sources': ['source1']
        }
        
        process_batch(image_paths, test_config)
        
        # Verify API was called once with all images
        assert mock_api.call_count == 1
        
        # Verify JSON was saved for each image
        assert mock_save.call_count == 3
    
    @patch('src.annotate.save_json')
    @patch('src.annotate.call_metatron_api_with_retry')
    @patch('src.annotate.encode_image_to_base64')
    def test_process_batch_saves_same_summary(self, mock_encode, mock_api, mock_save, test_config, tmp_path):
        """Test that same summary is saved to all frames in batch."""
        image_paths = []
        for i in range(2):
            img_path = tmp_path / f"test_{i}.png"
            img_path.write_bytes(b"fake image")
            image_paths.append(img_path)
        
        mock_encode.return_value = "base64data"
        mock_api.return_value = {
            'summary': 'Test summary',
            'sources': ['source1']
        }
        
        process_batch(image_paths, test_config)
        
        # Verify all saved annotations have the same summary
        for call in mock_save.call_args_list:
            annotation = call[0][1]
            assert annotation['summary'] == 'Test summary'
            assert annotation['batch_size'] == 2
    
    @patch('src.annotate.encode_image_to_base64')
    def test_process_batch_handles_encoding_failure(self, mock_encode, test_config, tmp_path):
        """Test batch processing handles encoding failures."""
        image_paths = [tmp_path / "test.png"]
        image_paths[0].write_bytes(b"fake image")
        
        mock_encode.side_effect = Exception("Encoding failed")
        
        # Should not raise exception, just log error
        process_batch(image_paths, test_config)
    
    @patch('src.annotate.call_metatron_api_with_retry')
    @patch('src.annotate.encode_image_to_base64')
    def test_process_batch_handles_api_failure(self, mock_encode, mock_api, test_config, tmp_path):
        """Test batch processing handles API failures."""
        image_paths = [tmp_path / "test.png"]
        image_paths[0].write_bytes(b"fake image")
        
        mock_encode.return_value = "base64data"
        mock_api.side_effect = Exception("API failed")
        
        # Should not raise exception, just log error
        process_batch(image_paths, test_config)
    
    @patch('src.annotate.encode_image_to_base64')
    def test_process_batch_skips_when_no_images(self, mock_encode, test_config):
        """Test that batch processing is skipped when no images."""
        # All images fail to encode
        mock_encode.side_effect = Exception("Failed")
        
        image_paths = [Path("test.png")]
        
        # Should complete without error
        process_batch(image_paths, test_config)


class TestFrameAnnotation:
    """Tests for frame annotation."""
    
    @pytest.fixture
    def test_config(self, tmp_path):
        """Provide test configuration."""
        return {
            'root_dir': str(tmp_path),
            'annotation': {
                'api_url': 'https://example.com/api',
                'prompt': 'test prompt',
                'timeout_sec': 30,
                'json_suffix': '.json',
                'batch_size': 4
            }
        }
    
    @patch('src.annotate.process_batch')
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_processes_unannotated(self, mock_daily_dir, mock_json_path, 
                                                    mock_process, test_config, tmp_path):
        """Test that unannotated frames are processed."""
        # Setup daily directory
        daily_dir = tmp_path / 'frames' / '2025-11-01'
        daily_dir.mkdir(parents=True)
        mock_daily_dir.return_value = daily_dir
        
        # Create unannotated PNG files
        for i in range(5):
            png_file = daily_dir / f'2025110{i}_100000.png'
            png_file.write_bytes(b'fake image')
        
        # Mock json_path to return non-existent files
        mock_json_path.side_effect = lambda p, suffix: p.with_suffix('.json')
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        assert count == 5
        mock_process.assert_called_once()
    
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_no_directory(self, mock_daily_dir, test_config, tmp_path):
        """Test annotation when directory doesn't exist."""
        mock_daily_dir.return_value = tmp_path / 'nonexistent'
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        assert count == 0
    
    @patch('src.annotate.process_batch')
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_skips_annotated(self, mock_daily_dir, mock_json_path,
                                             mock_process, test_config, tmp_path):
        """Test that already annotated frames are skipped."""
        daily_dir = tmp_path / 'frames' / '2025-11-01'
        daily_dir.mkdir(parents=True)
        mock_daily_dir.return_value = daily_dir
        
        # Create PNG and JSON files (already annotated)
        png_file = daily_dir / '20251101_100000.png'
        png_file.write_bytes(b'fake image')
        json_file = daily_dir / '20251101_100000.json'
        json_file.write_text('{"summary": "test"}')
        
        mock_json_path.return_value = json_file
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        assert count == 0
        mock_process.assert_not_called()
    
    @patch('src.annotate.process_batch')
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_checks_yesterday(self, mock_daily_dir, mock_json_path,
                                              mock_process, test_config, tmp_path):
        """Test that yesterday's folder is checked for unannotated frames."""
        # Create yesterday's directory
        yesterday_dir = tmp_path / 'frames' / '2025-10-31'
        yesterday_dir.mkdir(parents=True)
        
        # Create today's directory
        today_dir = tmp_path / 'frames' / '2025-11-01'
        today_dir.mkdir(parents=True)
        
        def get_daily_side_effect(root, date):
            if date.day == 31:
                return yesterday_dir
            return today_dir
        
        mock_daily_dir.side_effect = get_daily_side_effect
        
        # Create unannotated frame in yesterday's dir
        png_file = yesterday_dir / '20251031_235900.png'
        png_file.write_bytes(b'fake image')
        
        mock_json_path.side_effect = lambda p, suffix: p.with_suffix('.json')
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        assert count == 1
    
    @patch('src.annotate.process_batch')
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_processes_in_batches(self, mock_daily_dir, mock_json_path,
                                                   mock_process, test_config, tmp_path):
        """Test that frames are processed in configured batch size."""
        daily_dir = tmp_path / 'frames' / '2025-11-01'
        daily_dir.mkdir(parents=True)
        mock_daily_dir.return_value = daily_dir
        
        # Create 10 unannotated frames (batch_size is 4)
        for i in range(10):
            png_file = daily_dir / f'20251101_10{i:02d}00.png'
            png_file.write_bytes(b'fake image')
        
        mock_json_path.side_effect = lambda p, suffix: p.with_suffix('.json')
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        assert count == 10
        # Should be called 3 times: batch of 4, batch of 4, batch of 2
        assert mock_process.call_count == 3
    
    @patch('src.annotate.process_batch')
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_annotates_less_than_batch_size(self, mock_daily_dir, mock_json_path,
                                                            mock_process, test_config, tmp_path):
        """Test annotation proceeds even with fewer frames than batch_size."""
        daily_dir = tmp_path / 'frames' / '2025-11-01'
        daily_dir.mkdir(parents=True)
        mock_daily_dir.return_value = daily_dir
        
        # Create 2 frames (batch_size is 4)
        for i in range(2):
            png_file = daily_dir / f'2025110{i}_100000.png'
            png_file.write_bytes(b'fake image')
        
        mock_json_path.side_effect = lambda p, suffix: p.with_suffix('.json')
        
        count = annotate_frames(test_config, datetime(2025, 11, 1))
        
        # Should still process the 2 frames
        assert count == 2
        mock_process.assert_called_once()
    
    @patch('src.annotate.get_json_path')
    @patch('src.annotate.get_daily_dir')
    def test_annotate_frames_sorts_chronologically(self, mock_daily_dir, mock_json_path, 
                                                   test_config, tmp_path):
        """Test that frames are sorted chronologically before processing."""
        daily_dir = tmp_path / 'frames' / '2025-11-01'
        daily_dir.mkdir(parents=True)
        mock_daily_dir.return_value = daily_dir
        
        # Create frames in non-chronological order
        for timestamp in ['20251101_120000', '20251101_100000', '20251101_110000']:
            png_file = daily_dir / f'{timestamp}.png'
            png_file.write_bytes(b'fake image')
        
        mock_json_path.side_effect = lambda p, suffix: p.with_suffix('.json')
        
        with patch('src.annotate.process_batch') as mock_process:
            annotate_frames(test_config, datetime(2025, 11, 1))
            
            # Verify batch contains chronologically sorted frames
            batch = mock_process.call_args[0][0]
            filenames = [f.name for f in batch]
            assert filenames == sorted(filenames)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

