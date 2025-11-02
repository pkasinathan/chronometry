"""Daily digest generation module for Chronometry."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

from common import load_config, get_daily_dir, save_json, load_json, format_date
from timeline import load_annotations, group_activities, calculate_stats
from token_usage import TokenUsageTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def call_copilot_api(prompt: str, config: dict, max_tokens: int = None, context: str = None) -> str:
    """Call the Copilot API for text generation."""
    try:
        # Get digest config
        digest_config = config.get('digest', {})
        model = digest_config.get('model', 'gpt-4o')
        temperature = digest_config.get('temperature', 0.7)
        if max_tokens is None:
            max_tokens = digest_config.get('max_tokens_default', 500)
        
        json_payload = {
            "model": model,
            "temperature": temperature,
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
        
        # Get API URL from digest config
        ncp_project_id = digest_config.get('ncp_project_id', 'prabhuai')
        api_base_url = digest_config.get('api_url', 'https://copilotdpjava.vip.us-east-1.prod.cloud.netflix.net:8443')
        
        # Construct the full API URL
        api_url = f"{api_base_url}/{ncp_project_id}/v1/chat/completions"
        
        # Create the curl command
        cmd = [
            "metatron", "curl", "-a", "copilotdpjava",
            "-X", "POST",
            api_url,
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
            content = response["choices"][0]["message"]["content"]
            
            # Extract token usage if available
            usage = response.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Log token usage
            if tokens_used > 0:
                tracker = TokenUsageTracker(config['root_dir'])
                tracker.log_tokens(
                    api_type='digest',
                    tokens=tokens_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    context=context
                )
            
            # Return content and token info
            return {
                "content": content,
                "tokens": tokens_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
        else:
            logger.error(f"Unexpected API response: {response}")
            return {
                "content": "Error: Invalid API response",
                "tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Copilot API call timed out")
        return {
            "content": "Error: API timeout",
            "tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    except Exception as e:
        logger.error(f"Error calling Copilot API: {e}")
        return {
            "content": f"Error generating summary: {str(e)}",
            "tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }


def generate_category_summaries(activities: List[Dict], config: dict) -> Tuple[Dict[str, Dict], int]:
    """Generate summaries for each activity category.
    
    Returns:
        tuple: (category_summaries dict, total_tokens_used int)
    """
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
    total_tokens = 0
    
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
        
        # Get max tokens from config
        max_tokens_category = config.get('digest', {}).get('max_tokens_category', 200)
        result = call_copilot_api(prompt, config, max_tokens=max_tokens_category, context=f"Category: {category}")
        total_tokens += result['tokens']
        
        category_summaries[category] = {
            'summary': result['content'],
            'count': len(activities_list),
            'duration_minutes': int(category_duration[category]),
            'icon': activities_list[0]['icon'],
            'color': activities_list[0]['color']
        }
    
    return category_summaries, total_tokens


def generate_overall_summary(activities: List[Dict], stats: Dict, config: dict) -> Tuple[str, int]:
    """Generate an overall summary of the day.
    
    Returns:
        tuple: (summary text, tokens_used int)
    """
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
    
    # Get max tokens from config
    max_tokens_overall = config.get('digest', {}).get('max_tokens_overall', 300)
    result = call_copilot_api(prompt, config, max_tokens=max_tokens_overall, context="Overall summary")
    return result['content'], result['tokens']


def generate_daily_digest(date: datetime, config: dict) -> Dict:
    """Generate a complete daily digest."""
    root_dir = config['root_dir']
    daily_dir = get_daily_dir(root_dir, date)
    
    if not daily_dir.exists():
        logger.info(f"No data found for {format_date(date)}")
        return {
            'date': format_date(date),
            'error': 'No data available',
            'overall_summary': 'No activities recorded for this day.',
            'category_summaries': {},
            'stats': {}
        }
    
    # Load annotations and generate activities
    logger.info(f"Loading annotations for {format_date(date)}...")
    annotations = load_annotations(daily_dir)
    
    if not annotations:
        return {
            'date': format_date(date),
            'error': 'No annotations',
            'overall_summary': 'No activities recorded for this day.',
            'category_summaries': {},
            'stats': {}
        }
    
    logger.info(f"Found {len(annotations)} annotations")
    
    # Group into activities using config
    activities = group_activities(annotations, config=config)
    stats = calculate_stats(activities)
    
    logger.info(f"Generating digest for {len(activities)} activities...")
    
    # Generate category summaries
    category_summaries, category_tokens = generate_category_summaries(activities, config)
    
    # Generate overall summary
    overall_summary, overall_tokens = generate_overall_summary(activities, stats, config)
    
    # Calculate total token usage
    total_tokens = category_tokens + overall_tokens
    logger.info(f"Digest generated using {total_tokens} tokens")
    
    # Create digest (no token_usage field - that's tracked separately now)
    digest = {
        'date': format_date(date),
        'overall_summary': overall_summary,
        'category_summaries': category_summaries,
        'stats': stats,
        'total_activities': len(activities)
    }
    
    # Cache the digest
    cache_dir = Path(root_dir) / 'digests'
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"digest_{format_date(date)}.json"
    # Use helper to save JSON
    save_json(cache_file, digest)
    logger.info(f"Digest cached to {cache_file}")
    
    return digest


def load_cached_digest(date: datetime, config: dict) -> Dict:
    """Load a cached digest if available."""
    root_dir = config['root_dir']
    cache_dir = Path(root_dir) / 'digests'
    cache_file = cache_dir / f"digest_{format_date(date)}.json"
    
    if cache_file.exists():
        try:
            # Use helper to load JSON
            return load_json(cache_file)
        except Exception as e:
            logger.warning(f"Error loading cached digest: {e}")
    
    return None


def get_or_generate_digest(date: datetime, config: dict, force_regenerate: bool = False) -> Dict:
    """Get digest from cache or generate a new one."""
    if not force_regenerate:
        cached = load_cached_digest(date, config)
        if cached:
            logger.info(f"Using cached digest for {format_date(date)}")
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

