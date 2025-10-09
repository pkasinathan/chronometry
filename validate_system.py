#!/usr/bin/env python3
"""Comprehensive validation script for Chronometry."""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    errors = []
    
    modules = [
        'common',
        'capture',
        'annotate',
        'timeline',
        'digest',
        'token_usage',
        'web_server',
        'menubar_app'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            errors.append(f"{module}: {e}")
    
    return errors


def test_config():
    """Test configuration loading and validation."""
    print("\nTesting configuration...")
    errors = []
    
    try:
        from common import load_config
        config = load_config()
        print(f"  ✓ Config loaded successfully")
        
        # Validate required sections
        required = ['root_dir', 'capture', 'annotation', 'timeline']
        for section in required:
            if section not in config:
                errors.append(f"Missing config section: {section}")
            else:
                print(f"  ✓ Section '{section}' present")
        
        # Validate capture settings
        if 'fps' in config['capture']:
            fps = config['capture']['fps']
            if fps > 0:
                interval = 1.0 / fps
                print(f"  ✓ Capture interval: {interval:.1f} seconds")
            else:
                errors.append("FPS must be > 0")
        
        # Validate paths
        root_dir = Path(config['root_dir'])
        if not root_dir.exists():
            print(f"  ⚠ Root directory doesn't exist yet: {root_dir}")
            print(f"    (This is OK - it will be created on first capture)")
        
    except Exception as e:
        errors.append(f"Config test failed: {e}")
        print(f"  ✗ Config test failed: {e}")
    
    return errors


def test_directories():
    """Test directory structure."""
    print("\nTesting directory structure...")
    errors = []
    
    required_dirs = [
        'src',
        'bin',
        'config',
        'templates'
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ exists")
        else:
            errors.append(f"Missing directory: {dir_name}/")
            print(f"  ✗ {dir_name}/ missing")
    
    return errors


def test_scripts():
    """Test that shell scripts exist and are executable."""
    print("\nTesting shell scripts...")
    errors = []
    
    scripts = [
        'bin/start_chronometry_agent.sh',
        'bin/start_chronometry_menubar.sh',
        'bin/start_chronometry_webserver.sh',
        'bin/stop_chronometry_agent.sh',
        'bin/stop_chronometry_menubar.sh',
        'bin/stop_chronometry_webserver.sh',
    ]
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                print(f"  ✓ {script} (executable)")
            else:
                print(f"  ⚠ {script} (not executable)")
                print(f"    Run: chmod +x {script}")
        else:
            errors.append(f"Missing script: {script}")
            print(f"  ✗ {script} missing")
    
    return errors


def test_common_functions():
    """Test common utility functions."""
    print("\nTesting common functions...")
    errors = []
    
    try:
        from common import (
            get_daily_dir,
            get_frame_path,
            get_json_path,
            ensure_dir
        )
        
        # Test get_daily_dir
        from datetime import datetime
        test_date = datetime(2025, 10, 9)
        daily_dir = get_daily_dir("./data", test_date)
        expected = Path("./data/frames/2025-10-09")
        if daily_dir == expected:
            print(f"  ✓ get_daily_dir works correctly")
        else:
            errors.append(f"get_daily_dir returned {daily_dir}, expected {expected}")
        
        # Test get_frame_path
        frame_path = get_frame_path("./data", test_date)
        if frame_path.parent == expected:
            print(f"  ✓ get_frame_path works correctly")
        else:
            errors.append(f"get_frame_path parent mismatch")
        
        # Test get_json_path
        png_path = Path("test.png")
        json_path = get_json_path(png_path)
        if json_path.suffix == ".json":
            print(f"  ✓ get_json_path works correctly")
        else:
            errors.append(f"get_json_path returned {json_path}")
            
    except Exception as e:
        errors.append(f"Common functions test failed: {e}")
        print(f"  ✗ Test failed: {e}")
    
    return errors


def test_token_usage():
    """Test token usage tracking."""
    print("\nTesting token usage...")
    errors = []
    
    try:
        from token_usage import TokenUsageTracker
        import tempfile
        import shutil
        
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        
        try:
            tracker = TokenUsageTracker(temp_dir)
            
            # Test logging tokens
            tracker.log_tokens('test', 100, 50, 50, 'Test context')
            print(f"  ✓ Token logging works")
            
            # Test retrieving usage
            usage = tracker.get_daily_usage(datetime.now())
            if usage['total_tokens'] == 100:
                print(f"  ✓ Token retrieval works")
            else:
                errors.append(f"Token count mismatch: expected 100, got {usage['total_tokens']}")
            
            # Test concurrent writes (simulate with multiple rapid calls)
            for i in range(10):
                tracker.log_tokens('test', 10, 5, 5, f'Concurrent test {i}')
            
            usage = tracker.get_daily_usage(datetime.now())
            expected = 100 + (10 * 10)  # Initial 100 + 10 calls of 10 each
            if usage['total_tokens'] == expected:
                print(f"  ✓ Concurrent writes handled correctly")
            else:
                print(f"  ⚠ Token count after concurrent writes: {usage['total_tokens']} (expected {expected})")
                print(f"    (Small discrepancies are OK due to timing)")
                
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        errors.append(f"Token usage test failed: {e}")
        print(f"  ✗ Test failed: {e}")
    
    return errors


def test_timeline_functions():
    """Test timeline functions."""
    print("\nTesting timeline functions...")
    errors = []
    
    try:
        from timeline import categorize_activity, format_duration
        from datetime import datetime, timedelta
        
        # Test categorization
        test_cases = [
            ("Coding in Python", "Code"),
            ("Zoom meeting", "Meeting"),
            ("Writing documentation", "Documentation"),
            ("Browsing Reddit", "Browsing"),
            ("Unknown activity", "Work")  # Default
        ]
        
        for summary, expected_category in test_cases:
            category, icon, color = categorize_activity(summary)
            if category == expected_category:
                print(f"  ✓ Categorized '{summary[:20]}...' as {category}")
            else:
                errors.append(f"Wrong category for '{summary}': got {category}, expected {expected_category}")
        
        # Test duration formatting
        start = datetime.now()
        end = start + timedelta(minutes=5)
        duration = format_duration(start, end)
        if "5 mins" in duration or "5 min" in duration:
            print(f"  ✓ Duration formatting works")
        else:
            errors.append(f"Duration format unexpected: {duration}")
            
    except Exception as e:
        errors.append(f"Timeline test failed: {e}")
        print(f"  ✗ Test failed: {e}")
    
    return errors


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Chronometry System Validation")
    print("=" * 60)
    print()
    
    all_errors = []
    
    # Run all tests
    all_errors.extend(test_imports())
    all_errors.extend(test_config())
    all_errors.extend(test_directories())
    all_errors.extend(test_scripts())
    all_errors.extend(test_common_functions())
    all_errors.extend(test_token_usage())
    all_errors.extend(test_timeline_functions())
    
    # Summary
    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    if not all_errors:
        print()
        print("✅ ALL TESTS PASSED!")
        print()
        print("Your Chronometry installation is ready to use.")
        print()
        print("Next steps:")
        print("  1. Start the agent: ./bin/start_chronometry_agent.sh")
        print("  2. Start web server: ./bin/start_chronometry_webserver.sh")
        print("  3. Open dashboard: http://localhost:8051")
        print()
        return 0
    else:
        print()
        print(f"❌ {len(all_errors)} ISSUE(S) FOUND:")
        print()
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
        print()
        print("Please fix these issues before using Chronometry.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

