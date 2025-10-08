"""Daily digest generation module for Chronometry."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

from common import load_config, get_daily_dir
from timeline import load_annotations, group_activities, calculate_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def call_copilot_api(prompt: str, max_tokens: int = 500) -> str:
    """Call the Copilot API for text generation."""
    try:
        json_payload = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant that creates concise, professional summaries of work activities. Generate clear, well-structured summaries that highlight key accomplishments and patterns."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Get NCP project ID from config or use default
        ncp_project_id = "prabhuai"
        
        # Create the curl command
        cmd = [
            "metatron", "curl", "-a", "copilotdpjava",
            "-X", "POST",
            f"https://copilotdpjava.vip.us-east-1.prod.cloud.netflix.net:8443/{ncp_project_id}/v1/chat/completions",
            "-d", json.dumps(json_payload),
            "-H", "Content-Type: application/json"
        ]
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Copilot API call failed: {result.stderr}")
            return "Error generating summary"
        
        # Parse the response
        response = json.loads(result.stdout)
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            logger.error(f"Unexpected API response: {response}")
            return "Error: Invalid API response"
            
    except subprocess.TimeoutExpired:
        logger.error("Copilot API call timed out")
        return "Error: API timeout"
    except Exception as e:
        logger.error(f"Error calling Copilot API: {e}")
        return f"Error generating summary: {str(e)}"


def generate_category_summaries(activities: List[Dict]) -> Dict[str, Dict]:
    """Generate summaries for each activity category."""
    # Group activities by category
    category_activities = defaultdict(list)
    category_duration = defaultdict(int)
    
    for activity in activities:
        category = activity['category']
        category_activities[category].append(activity)
        
        # Calculate duration
        start = activity['start_time']
        end = activity['end_time']
        duration = (end - start).total_seconds() / 60
        category_duration[category] += duration
    
    # Generate summary for each category
    category_summaries = {}
    
    for category, activities_list in category_activities.items():
        # Prepare prompt for the category
        activity_descriptions = []
        for idx, activity in enumerate(activities_list[:10], 1):  # Limit to 10 activities per category
            summary = activity['summary'][:200]  # Limit summary length
            activity_descriptions.append(f"{idx}. {summary}")
        
        if len(activities_list) > 10:
            activity_descriptions.append(f"... and {len(activities_list) - 10} more activities")
        
        prompt = f"""Summarize the following {category} activities from today's work in 2-3 sentences. Focus on key accomplishments and patterns:

{chr(10).join(activity_descriptions)}

Provide a concise, professional summary."""
        
        summary_text = call_copilot_api(prompt, max_tokens=200)
        
        category_summaries[category] = {
            'summary': summary_text,
            'count': len(activities_list),
            'duration_minutes': int(category_duration[category]),
            'icon': activities_list[0]['icon'],
            'color': activities_list[0]['color']
        }
    
    return category_summaries


def generate_overall_summary(activities: List[Dict], stats: Dict) -> str:
    """Generate an overall summary of the day."""
    # Prepare high-level information
    total_activities = len(activities)
    focus_percentage = stats['focus_percentage']
    category_breakdown = stats['category_breakdown']
    
    # Get top categories
    top_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
    top_categories_str = ", ".join([f"{cat} ({int(mins)}m)" for cat, mins in top_categories])
    
    # Sample some key activities
    key_activities = []
    for activity in activities[:5]:  # Take first 5 activities as examples
        key_activities.append(f"• {activity['category']}: {activity['summary'][:100]}")
    
    prompt = f"""Generate a brief, professional summary (3-4 sentences) of today's work activities:

**Statistics:**
- Total activities: {total_activities}
- Focus percentage: {focus_percentage}%
- Top categories: {top_categories_str}

**Sample activities:**
{chr(10).join(key_activities)}

Create an engaging summary that highlights productivity and key focus areas."""
    
    return call_copilot_api(prompt, max_tokens=300)


def generate_daily_digest(date: datetime, config: dict) -> Dict:
    """Generate a complete daily digest."""
    root_dir = config['root_dir']
    daily_dir = get_daily_dir(root_dir, date)
    
    if not daily_dir.exists():
        logger.info(f"No data found for {date.strftime('%Y-%m-%d')}")
        return {
            'date': date.strftime('%Y-%m-%d'),
            'error': 'No data available',
            'overall_summary': 'No activities recorded for this day.',
            'category_summaries': {},
            'stats': {}
        }
    
    # Load annotations and generate activities
    logger.info(f"Loading annotations for {date.strftime('%Y-%m-%d')}...")
    annotations = load_annotations(daily_dir)
    
    if not annotations:
        return {
            'date': date.strftime('%Y-%m-%d'),
            'error': 'No annotations',
            'overall_summary': 'No activities recorded for this day.',
            'category_summaries': {},
            'stats': {}
        }
    
    logger.info(f"Found {len(annotations)} annotations")
    
    # Group into activities
    activities = group_activities(annotations, gap_minutes=5)
    stats = calculate_stats(activities)
    
    logger.info(f"Generating digest for {len(activities)} activities...")
    
    # Generate category summaries
    category_summaries = generate_category_summaries(activities)
    
    # Generate overall summary
    overall_summary = generate_overall_summary(activities, stats)
    
    # Create digest
    digest = {
        'date': date.strftime('%Y-%m-%d'),
        'overall_summary': overall_summary,
        'category_summaries': category_summaries,
        'stats': stats,
        'total_activities': len(activities)
    }
    
    # Cache the digest
    cache_dir = Path(root_dir) / 'digests'
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"digest_{date.strftime('%Y-%m-%d')}.json"
    with open(cache_file, 'w') as f:
        json.dump(digest, f, indent=2)
    
    logger.info(f"Digest cached to {cache_file}")
    
    return digest


def load_cached_digest(date: datetime, config: dict) -> Dict:
    """Load a cached digest if available."""
    root_dir = config['root_dir']
    cache_dir = Path(root_dir) / 'digests'
    cache_file = cache_dir / f"digest_{date.strftime('%Y-%m-%d')}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading cached digest: {e}")
    
    return None


def get_or_generate_digest(date: datetime, config: dict, force_regenerate: bool = False) -> Dict:
    """Get digest from cache or generate a new one."""
    if not force_regenerate:
        cached = load_cached_digest(date, config)
        if cached:
            logger.info(f"Using cached digest for {date.strftime('%Y-%m-%d')}")
            return cached
    
    return generate_daily_digest(date, config)


def main():
    """Main entry point for testing."""
    try:
        config = load_config()
        
        # Generate digest for today
        today = datetime.now()
        digest = generate_daily_digest(today, config)
        
        print(f"\n{'='*60}")
        print(f"Daily Digest for {digest['date']}")
        print(f"{'='*60}\n")
        
        print(f"Overall Summary:\n{digest['overall_summary']}\n")
        
        print(f"\nCategory Summaries:")
        for category, data in digest['category_summaries'].items():
            print(f"\n{data['icon']} {category} ({data['count']} activities, {data['duration_minutes']}m):")
            print(f"  {data['summary']}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

