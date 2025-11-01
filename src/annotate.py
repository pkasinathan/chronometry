"""Annotation module for Chronometry using Metatron API."""

import os
import json
import base64
import subprocess
import tempfile
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import urlparse
from common import (
    load_config, get_daily_dir, get_json_path
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def call_metatron_api(images: List[Dict], config: dict) -> Dict:
    """Call Metatron API with batch of images.
    
    Args:
        images: List of image dictionaries with base64_data
        config: Configuration dictionary
        
    Returns:
        API response dictionary with 'summary' and 'sources' fields
        
    Raises:
        ValueError: If API URL is invalid
        Exception: If API call fails
    """
    annotation_config = config['annotation']
    
    # Get API settings
    api_url = annotation_config['api_url']
    prompt = annotation_config['prompt']
    timeout = annotation_config.get('timeout_sec', 30)
    
    # SECURITY: Validate API URL to prevent command injection
    parsed_url = urlparse(api_url)
    if parsed_url.scheme not in ['https', 'http']:
        raise ValueError(f"Invalid API URL scheme: {parsed_url.scheme}. Must be http or https.")
    if not parsed_url.netloc:
        raise ValueError(f"Invalid API URL: {api_url}. Missing network location.")
    
    # Prepare request payload
    payload = {
        "prompt": prompt,
        "files": images
    }
    
    # Use metatron curl command
    # Write payload to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        temp_file = f.name
    
    try:
        # Build metatron curl command
        cmd = [
            '/usr/local/bin/metatron', 'curl', '-a', 'aiopsproxy',
            '-X', 'POST',
            api_url,
            '-d', f'@{temp_file}'
        ]
        
        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            raise Exception(f"Metatron command failed: {result.stderr}")
        
        # Parse and validate JSON response
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse API response as JSON: {e}\n"
                f"Response preview: {result.stdout[:500]}"
            )
        
        # Validate response structure
        if not isinstance(response, dict):
            raise Exception("Invalid API response format: expected dictionary")
        
        # Validate and ensure required fields exist
        if 'summary' not in response:
            logger.warning("API response missing 'summary' field, using empty string")
            response['summary'] = ""
        elif not isinstance(response['summary'], str):
            logger.warning(f"API response 'summary' is not a string (type: {type(response['summary'])}), converting")
            response['summary'] = str(response['summary'])
        
        if 'sources' not in response:
            logger.warning("API response missing 'sources' field, using empty list")
            response['sources'] = []
        elif not isinstance(response['sources'], list):
            logger.warning(f"API response 'sources' is not a list (type: {type(response['sources'])}), converting")
            response['sources'] = []
        
        return response
    
    finally:
        # Clean up temp file
        os.unlink(temp_file)


def call_metatron_api_with_retry(images: List[Dict], config: dict, max_retries: int = 3) -> Dict:
    """Call Metatron API with retry logic and exponential backoff.
    
    Args:
        images: List of image dictionaries with base64_data
        config: Configuration dictionary
        max_retries: Maximum number of retry attempts
        
    Returns:
        API response dictionary
        
    Raises:
        Exception: If all retry attempts fail
    """
    for attempt in range(max_retries):
        try:
            return call_metatron_api(images, config)
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt, re-raise the exception
                logger.error(f"API call failed after {max_retries} attempts: {e}")
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


def process_batch(image_paths: List[Path], config: dict):
    """Process a batch of images through the API with retry logic."""
    annotation_config = config['annotation']
    json_suffix = annotation_config.get('json_suffix', '.json')
    
    # Prepare image data for API
    images = []
    for idx, image_path in enumerate(image_paths):
        try:
            base64_data = encode_image_to_base64(image_path)
            images.append({
                "name": f"frame{idx}",
                "content_type": "image/png",
                "base64_data": base64_data
            })
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            continue
    
    if not images:
        logger.error("No images to process in batch")
        return
    
    try:
        # Call API with retry logic
        logger.info(f"Calling Metatron API with {len(images)} images...")
        result = call_metatron_api_with_retry(images, config)
        
        # Save results
        # Assuming API returns a single summary for the batch
        # Save the same summary for each image in the batch
        for image_path in image_paths:
            json_path = get_json_path(image_path, json_suffix)
            
            # Create result structure
            json_data = {
                "timestamp": image_path.stem,
                "image_file": image_path.name,
                "summary": result.get("summary", ""),
                "sources": result.get("sources", []),
                "batch_size": len(image_paths)
            }
            
            # Save JSON
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            logger.info(f"Saved annotation: {json_path.name}")
            
    except Exception as e:
        logger.error(f"Error processing batch: {e}", exc_info=True)


def annotate_frames(config: dict, date: datetime = None) -> int:
    """Annotate all unannotated frames for a given date.
    
    Also checks yesterday's folder for any remaining unannotated frames to handle
    edge case where frames captured near midnight don't reach batch_size threshold.
    
    Returns:
        Number of frames that were annotated (0 if waiting for batch_size)
    """
    root_dir = config['root_dir']
    annotation_config = config['annotation']
    batch_size = annotation_config.get('batch_size', 1)
    json_suffix = annotation_config.get('json_suffix', '.json')
    
    # Get directory for the date
    if date is None:
        date = datetime.now()
    
    # Collect unannotated frames from multiple directories
    unannotated = []
    dirs_to_check = []
    
    # Always check yesterday's folder first (to catch cross-midnight frames)
    yesterday = date - timedelta(days=1)
    yesterday_dir = get_daily_dir(root_dir, yesterday)
    if yesterday_dir.exists():
        dirs_to_check.append((yesterday, yesterday_dir))
    
    # Then check today's folder
    daily_dir = get_daily_dir(root_dir, date)
    if daily_dir.exists():
        dirs_to_check.append((date, daily_dir))
    
    if not dirs_to_check:
        logger.info(f"No frames found for {date.strftime('%Y-%m-%d')} or previous day")
        return 0
    
    # Find all PNG files without corresponding JSON across checked directories
    for check_date, check_dir in dirs_to_check:
        png_files = sorted(check_dir.glob("*.png"))
        dir_unannotated = [
            png_path for png_path in png_files 
            if not get_json_path(png_path, json_suffix).exists()
        ]
        if dir_unannotated:
            logger.info(f"Found {len(dir_unannotated)} unannotated frames in {check_date.strftime('%Y-%m-%d')}")
            unannotated.extend(dir_unannotated)
    
    if not unannotated:
        logger.info(f"All frames already annotated")
        return 0
    
    # Note: We'll annotate even if we have fewer than batch_size frames
    # This ensures frames don't wait indefinitely (e.g., manual captures, end of day)
    # The API can handle any batch size from 1 to batch_size
    if len(unannotated) < batch_size:
        logger.info(f"Found {len(unannotated)} unannotated frames (less than batch_size={batch_size}), annotating anyway")
    
    # Sort all unannotated frames by timestamp to maintain chronological order
    unannotated.sort()
    
    logger.info(f"Found {len(unannotated)} total unannotated frames, processing in batches of {batch_size}")
    
    # Process in batches
    total_batches = (len(unannotated) + batch_size - 1) // batch_size
    for i in range(0, len(unannotated), batch_size):
        batch = unannotated[i:i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"Processing batch {batch_num}/{total_batches}")
        process_batch(batch, config)
    
    return len(unannotated)


def main():
    """Main entry point."""
    try:
        config = load_config()
        
        # Annotate today's frames by default
        annotate_frames(config)
        
        logger.info("Annotation process completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in annotation process: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
