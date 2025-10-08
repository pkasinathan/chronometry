"""Tests for annotate.py module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from annotate import encode_image_to_base64, call_metatron_api


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

