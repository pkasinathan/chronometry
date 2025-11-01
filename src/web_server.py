"""Chronometry Web Server - Modern Web Interface on Port 8051."""

import os
import json
import logging
import base64
import io
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional

from flask import Flask, jsonify, render_template, request, send_file, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
from PIL import Image

from common import load_config, get_daily_dir, get_frame_path
from timeline import load_annotations, categorize_activity, group_activities, calculate_stats
from digest import get_or_generate_digest
from token_usage import TokenUsageTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
# Since we're in src/, templates are in ../templates
import os
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
# SECRET_KEY will be set after config is loaded
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global config
config = None


def init_config():
    """Initialize configuration."""
    global config
    try:
        config = load_config()
        
        # Convert relative paths to absolute (since we're in src/)
        if 'root_dir' in config and not Path(config['root_dir']).is_absolute():
            project_root = Path(__file__).parent.parent
            config['root_dir'] = str(project_root / config['root_dir'])
        
        # Set Flask secret key from config
        server_config = config.get('server', {})
        app.config['SECRET_KEY'] = server_config.get('secret_key', 'chronometry-secret-key-2025')
        
        logger.info(f"Configuration loaded successfully. Root dir: {config.get('root_dir')}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/config')
def get_config():
    """Get current user-level configuration (exposed in UI)."""
    return jsonify({
        'capture': {
            'capture_interval_seconds': config['capture'].get('capture_interval_seconds', 900),
            'monitor_index': config['capture']['monitor_index'],
            'retention_days': config['capture']['retention_days']
        },
        'annotation': {
            'batch_size': config['annotation']['batch_size'],
            'prompt': config['annotation'].get('prompt', 'Summarize the type of task or activity shown in these images.')
        },
        'timeline': {
            'bucket_minutes': config['timeline']['bucket_minutes'],
            'exclude_keywords': config['timeline'].get('exclude_keywords', [])
        },
        'digest': {
            'interval_seconds': config.get('digest', {}).get('interval_seconds', 3600),
            'ncp_project_id': config.get('digest', {}).get('ncp_project_id', 'pkasichronometry')
        },
        'notifications': {
            'enabled': config.get('notifications', {}).get('enabled', True),
            'notify_before_capture': config.get('notifications', {}).get('notify_before_capture', True),
            'pre_capture_warning_seconds': config.get('notifications', {}).get('pre_capture_warning_seconds', 5),
            'pre_capture_sound': config.get('notifications', {}).get('pre_capture_sound', False)
        }
    })


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update user configuration while preserving comments and formatting.
    
    Only updates user_config.yaml (user-editable settings).
    System configs cannot be modified via API.
    """
    try:
        updates = request.json
        
        # Determine which config file to update
        user_config_path = Path('config/user_config.yaml')
        legacy_config_path = Path('config/config.yaml')
        
        # Use user_config.yaml if it exists, otherwise fall back to legacy
        if user_config_path.exists():
            config_path = str(user_config_path)
            logger.info("Updating user_config.yaml")
        else:
            config_path = str(legacy_config_path)
            logger.warning("Updating legacy config.yaml (consider migrating to split configs)")
        
        # Read the original file to preserve comments
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        # Parse the YAML to get structure
        import yaml
        with open(config_path, 'r') as f:
            current_config = yaml.safe_load(f)
        
        # Apply updates (only user-level settings)
        if 'capture' in updates:
            if 'capture' not in current_config:
                current_config['capture'] = {}
            current_config['capture'].update(updates['capture'])
        if 'annotation' in updates:
            if 'annotation' not in current_config:
                current_config['annotation'] = {}
            current_config['annotation'].update(updates['annotation'])
        if 'timeline' in updates:
            if 'timeline' not in current_config:
                current_config['timeline'] = {}
            current_config['timeline'].update(updates['timeline'])
        if 'digest' in updates:
            if 'digest' not in current_config:
                current_config['digest'] = {}
            current_config['digest'].update(updates['digest'])
        if 'notifications' in updates:
            if 'notifications' not in current_config:
                current_config['notifications'] = {}
            current_config['notifications'].update(updates['notifications'])
        
        # Update only the values in the original file, preserving comments
        import re
        updated_lines = []
        for line in lines:
            updated_line = line
            
            # Update capture settings
            if 'capture' in updates:
                if re.match(r'^\s+capture_interval_seconds:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['capture'].get('capture_interval_seconds', current_config['capture'].get('capture_interval_seconds', 900))}", line)
                elif re.match(r'^\s+monitor_index:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['capture'].get('monitor_index', current_config['capture']['monitor_index'])}", line)
                elif re.match(r'^\s+retention_days:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['capture'].get('retention_days', current_config['capture']['retention_days'])}", line)
            
            # Update annotation settings
            if 'annotation' in updates:
                if re.match(r'^\s+batch_size:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['annotation'].get('batch_size', current_config['annotation']['batch_size'])}", line)
                elif re.match(r'^\s+prompt:', line):
                    value = updates['annotation'].get('prompt', current_config['annotation'].get('prompt', ''))
                    # Escape quotes and handle multiline
                    value_escaped = value.replace('"', '\\"')
                    updated_line = f'  prompt: "{value_escaped}"\n'
            
            # Update timeline settings
            if 'timeline' in updates:
                if re.match(r'^\s+bucket_minutes:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['timeline'].get('bucket_minutes', current_config['timeline']['bucket_minutes'])}", line)
                elif re.match(r'^\s+exclude_keywords:', line):
                    keywords = updates['timeline'].get('exclude_keywords', current_config['timeline'].get('exclude_keywords', []))
                    if keywords:
                        keywords_str = ', '.join([f'"{k}"' for k in keywords])
                        updated_line = f'  exclude_keywords: [{keywords_str}]\n'
                    else:
                        updated_line = '  exclude_keywords: []\n'
            
            # Update digest settings
            if 'digest' in updates:
                if re.match(r'^\s+interval_seconds:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['digest'].get('interval_seconds', current_config['digest']['interval_seconds'])}", line)
                elif re.match(r'^\s+ncp_project_id:', line):
                    value = updates['digest'].get('ncp_project_id', current_config['digest']['ncp_project_id'])
                    updated_line = re.sub(r':\s*"?[\w-]+"?', f': "{value}"', line)
            
            # Update notification settings
            if 'notifications' in updates:
                if re.match(r'^\s+enabled:', line) and 'notifications:' in ''.join(lines[max(0, lines.index(line)-5):lines.index(line)]):
                    updated_line = re.sub(r':\s*\w+', f": {str(updates['notifications'].get('enabled', current_config.get('notifications', {}).get('enabled', True))).lower()}", line)
                elif re.match(r'^\s+notify_before_capture:', line):
                    updated_line = re.sub(r':\s*\w+', f": {str(updates['notifications'].get('notify_before_capture', current_config.get('notifications', {}).get('notify_before_capture', True))).lower()}", line)
                elif re.match(r'^\s+pre_capture_warning_seconds:', line):
                    updated_line = re.sub(r':\s*\d+', f": {updates['notifications'].get('pre_capture_warning_seconds', current_config.get('notifications', {}).get('pre_capture_warning_seconds', 5))}", line)
                elif re.match(r'^\s+pre_capture_sound:', line):
                    updated_line = re.sub(r':\s*\w+', f": {str(updates['notifications'].get('pre_capture_sound', current_config.get('notifications', {}).get('pre_capture_sound', False))).lower()}", line)
            
            updated_lines.append(updated_line)
        
        # Save updated config with comments preserved
        with open(config_path, 'w') as f:
            f.writelines(updated_lines)
        
        # Reload config
        init_config()
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get overall statistics across all days."""
    try:
        root_dir = config['root_dir']
        frames_dir = Path(root_dir) / 'frames'
        
        if not frames_dir.exists():
            return jsonify({
                'total_days': 0,
                'total_frames': 0,
                'total_activities': 0,
                'average_focus': 0
            })
        
        total_frames = 0
        total_activities = 0
        total_focus = 0
        days_count = 0
        
        for date_dir in frames_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            try:
                # Count frames
                json_files = list(date_dir.glob('*.json'))
                total_frames += len(json_files)
                
                # Load annotations and calculate stats
                annotations = load_annotations(date_dir)
                if annotations:
                    activities = group_activities(annotations, config=config)
                    stats = calculate_stats(activities)
                    total_activities += len(activities)
                    total_focus += stats['focus_percentage']
                    days_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing {date_dir}: {e}")
                continue
        
        return jsonify({
            'total_days': days_count,
            'total_frames': total_frames,
            'total_activities': total_activities,
            'average_focus': int(total_focus / days_count) if days_count > 0 else 0
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/timeline')
def get_timeline():
    """Get timeline data for a specific date or date range."""
    try:
        # Get query parameters
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        days = int(request.args.get('days', 1))  # Number of days to include
        
        root_dir = config['root_dir']
        
        # Parse start date
        start_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        all_activities = []
        
        # Collect activities for each day
        for i in range(days):
            current_date = start_date - timedelta(days=i)
            daily_dir = get_daily_dir(root_dir, current_date)
            
            if not daily_dir.exists():
                continue
            
            annotations = load_annotations(daily_dir)
            if annotations:
                activities = group_activities(annotations, config=config)
                
                # Add date info to each activity
                for activity in activities:
                    activity['date'] = current_date.strftime('%Y-%m-%d')
                    activity['start_time_str'] = activity['start_time'].isoformat()
                    activity['end_time_str'] = activity['end_time'].isoformat()
                    
                    # Remove datetime objects for JSON serialization
                    del activity['start_time']
                    del activity['end_time']
                    del activity['frames']  # Too large for API response
                
                all_activities.extend(activities)
        
        # Sort by time
        all_activities.sort(key=lambda x: x['start_time_str'], reverse=True)
        
        return jsonify({
            'activities': all_activities,
            'count': len(all_activities)
        })
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/timeline/<date>')
def get_timeline_by_date(date):
    """Get timeline data for a specific date with full details."""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        root_dir = config['root_dir']
        daily_dir = get_daily_dir(root_dir, date_obj)
        
        if not daily_dir.exists():
            return jsonify({
                'date': date,
                'activities': [],
                'stats': {}
            })
        
        # Load annotations
        annotations = load_annotations(daily_dir)
        
        if not annotations:
            return jsonify({
                'date': date,
                'activities': [],
                'stats': {}
            })
        
        # Group into activities
        activities = group_activities(annotations, config=config)
        stats = calculate_stats(activities)
        
        # Prepare activity data
        activity_data = []
        for activity in activities:
            activity_info = {
                'category': activity['category'],
                'icon': activity['icon'],
                'color': activity['color'],
                'start_time': activity['start_time'].isoformat(),
                'end_time': activity['end_time'].isoformat(),
                'summary': activity['summary'],
                'frame_count': len(activity['frames']),
                'duration_minutes': int((activity['end_time'] - activity['start_time']).total_seconds() / 60)
            }
            activity_data.append(activity_info)
        
        return jsonify({
            'date': date,
            'activities': activity_data,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting timeline for {date}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def search_activities():
    """Search activities across all dates."""
    try:
        query = request.args.get('q', '').lower()
        category = request.args.get('category', '')
        days = int(request.args.get('days', 7))  # Search last 7 days by default
        
        root_dir = config['root_dir']
        frames_dir = Path(root_dir) / 'frames'
        
        if not frames_dir.exists():
            return jsonify({'results': []})
        
        results = []
        
        # Search through recent days
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_dir = get_daily_dir(root_dir, date)
            
            if not daily_dir.exists():
                continue
            
            annotations = load_annotations(daily_dir)
            if not annotations:
                continue
            
            activities = group_activities(annotations, config=config)
            
            for activity in activities:
                # Apply filters
                summary_lower = activity['summary'].lower()
                
                if query and query not in summary_lower:
                    continue
                
                if category and activity['category'].lower() != category.lower():
                    continue
                
                # Add to results
                results.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'category': activity['category'],
                    'icon': activity['icon'],
                    'color': activity['color'],
                    'start_time': activity['start_time'].isoformat(),
                    'end_time': activity['end_time'].isoformat(),
                    'summary': activity['summary'],
                    'duration_minutes': int((activity['end_time'] - activity['start_time']).total_seconds() / 60)
                })
        
        return jsonify({
            'query': query,
            'category': category,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics')
def get_analytics():
    """Get detailed analytics and insights."""
    try:
        days = int(request.args.get('days', 7))
        
        root_dir = config['root_dir']
        
        # Collect data
        daily_stats = []
        category_totals = defaultdict(int)
        hourly_activity = defaultdict(int)
        token_usage_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_dir = get_daily_dir(root_dir, date)
            
            if not daily_dir.exists():
                continue
            
            annotations = load_annotations(daily_dir)
            if not annotations:
                continue
            
            activities = group_activities(annotations, config=config)
            stats = calculate_stats(activities)
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'focus_percentage': stats['focus_percentage'],
                'distraction_percentage': stats['distraction_percentage'],
                'total_activities': len(activities),
                'total_time': stats['total_time']
            })
            
            # Aggregate category data
            for activity in activities:
                duration = (activity['end_time'] - activity['start_time']).total_seconds() / 60
                category_totals[activity['category']] += duration
                
                # Hourly distribution
                hour = activity['start_time'].hour
                hourly_activity[hour] += duration
            
            # Get token usage from separate token tracking
            try:
                tracker = TokenUsageTracker(root_dir)
                usage = tracker.get_daily_usage(date)
                if usage['total_tokens'] > 0:
                    token_usage_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'digest_tokens': usage['by_type'].get('digest', 0),
                        'annotation_tokens': usage['by_type'].get('annotation', 0),
                        'total_tokens': usage['total_tokens']
                    })
            except Exception as e:
                logger.warning(f"Error loading token usage for {date}: {e}")
        
        # Convert to lists for JSON
        category_breakdown = [
            {'category': k, 'minutes': int(v)}
            for k, v in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        ]
        
        hourly_breakdown = [
            {'hour': h, 'minutes': int(hourly_activity.get(h, 0))}
            for h in range(24)
        ]
        
        # Sort token usage data by date
        token_usage_data.sort(key=lambda x: x['date'])
        
        return jsonify({
            'daily_stats': daily_stats,
            'category_breakdown': category_breakdown,
            'hourly_breakdown': hourly_breakdown,
            'token_usage': token_usage_data
        })
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/csv')
def export_csv():
    """Export timeline data as CSV."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        root_dir = config['root_dir']
        daily_dir = get_daily_dir(root_dir, date_obj)
        
        if not daily_dir.exists():
            return jsonify({'error': 'No data for this date'}), 404
        
        annotations = load_annotations(daily_dir)
        if not annotations:
            return jsonify({'error': 'No annotations found'}), 404
        
        activities = group_activities(annotations, config=config)
        
        # Create DataFrame
        data = []
        for activity in activities:
            data.append({
                'Date': date_str,
                'Category': activity['category'],
                'Start Time': activity['start_time'].strftime('%H:%M:%S'),
                'End Time': activity['end_time'].strftime('%H:%M:%S'),
                'Duration (minutes)': int((activity['end_time'] - activity['start_time']).total_seconds() / 60),
                'Summary': activity['summary']
            })
        
        df = pd.DataFrame(data)
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=timeline_{date_str}.csv'}
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/json')
def export_json():
    """Export timeline data as JSON."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        root_dir = config['root_dir']
        daily_dir = get_daily_dir(root_dir, date_obj)
        
        if not daily_dir.exists():
            return jsonify({'error': 'No data for this date'}), 404
        
        annotations = load_annotations(daily_dir)
        if not annotations:
            return jsonify({'error': 'No annotations found'}), 404
        
        activities = group_activities(annotations, config=config)
        stats = calculate_stats(activities)
        
        # Prepare export data
        export_data = {
            'date': date_str,
            'stats': stats,
            'activities': []
        }
        
        for activity in activities:
            export_data['activities'].append({
                'category': activity['category'],
                'start_time': activity['start_time'].isoformat(),
                'end_time': activity['end_time'].isoformat(),
                'duration_minutes': int((activity['end_time'] - activity['start_time']).total_seconds() / 60),
                'summary': activity['summary']
            })
        
        return jsonify(export_data)
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/frames')
def get_frames():
    """Get list of frames for a specific date."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        root_dir = config['root_dir']
        daily_dir = get_daily_dir(root_dir, date_obj)
        
        if not daily_dir.exists():
            return jsonify({'frames': []})
        
        frames = []
        json_files = sorted(daily_dir.glob('*.json'))
        
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            timestamp = json_file.stem
            frames.append({
                'timestamp': timestamp,
                'datetime': datetime.strptime(timestamp, '%Y%m%d_%H%M%S').isoformat(),
                'summary': data.get('summary', ''),
                'image_file': data.get('image_file', '')
            })
        
        return jsonify({'frames': frames})
    except Exception as e:
        logger.error(f"Error getting frames: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/frames/<date>/<timestamp>/image')
def get_frame_image(date, timestamp):
    """Get a specific frame image."""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        root_dir = config['root_dir']
        
        # Convert to absolute path if relative
        if not Path(root_dir).is_absolute():
            # Since we're in src/, navigate to project root first
            project_root = Path(__file__).parent.parent
            root_dir = str(project_root / root_dir)
        
        daily_dir = get_daily_dir(root_dir, date_obj)
        image_path = daily_dir / f"{timestamp}.png"
        
        if not image_path.exists():
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(str(image_path), mimetype='image/png')
    except Exception as e:
        logger.error(f"Error getting frame image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dates')
def get_available_dates():
    """Get list of dates with captured data."""
    try:
        root_dir = config['root_dir']
        frames_dir = Path(root_dir) / 'frames'
        
        if not frames_dir.exists():
            return jsonify({'dates': []})
        
        dates = []
        for date_dir in sorted(frames_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            try:
                # Validate date format
                datetime.strptime(date_dir.name, '%Y-%m-%d')
                
                # Count frames
                json_files = list(date_dir.glob('*.json'))
                
                dates.append({
                    'date': date_dir.name,
                    'frame_count': len(json_files)
                })
            except ValueError:
                continue
        
        return jsonify({'dates': dates})
    except Exception as e:
        logger.error(f"Error getting dates: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/digest')
@app.route('/api/digest/<date>')
def get_digest(date=None):
    """Get daily digest summary."""
    try:
        if date is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            date_obj = datetime.now()
        else:
            date_str = date
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        # Check if force regenerate is requested
        force_regenerate = request.args.get('force', 'false').lower() == 'true'
        
        # Get or generate digest
        digest = get_or_generate_digest(date_obj, config, force_regenerate=force_regenerate)
        
        return jsonify(digest)
    except Exception as e:
        logger.error(f"Error getting digest: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to Chronometry server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')


@socketio.on('subscribe_live')
def handle_subscribe_live():
    """Subscribe to live activity updates."""
    emit('subscribed', {'message': 'Subscribed to live updates'})


def broadcast_new_frame(frame_data):
    """Broadcast new frame to connected clients."""
    socketio.emit('new_frame', frame_data)


def broadcast_new_activity(activity_data):
    """Broadcast new activity to connected clients."""
    socketio.emit('new_activity', activity_data)


def main():
    """Main entry point for web server."""
    try:
        # Initialize configuration
        init_config()
        
        # Create templates directory if it doesn't exist
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("Chronometry Web Server")
        logger.info("=" * 60)
        logger.info(f"Starting server on http://localhost:8051")
        logger.info(f"Dashboard: http://localhost:8051")
        logger.info(f"API Docs: http://localhost:8051/api/health")
        logger.info("=" * 60)
        
        # Run server with config
        server_config = config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8051)
        debug = server_config.get('debug', True)
        
        logger.info(f"Starting server on http://{host}:{port}")
        
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        logger.error(f"Fatal error starting web server: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
