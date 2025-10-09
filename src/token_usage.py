"""Token usage tracking module for API calls."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """Track and store API token usage."""
    
    def __init__(self, root_dir: str):
        """Initialize token tracker.
        
        Args:
            root_dir: Root directory for data storage
        """
        self.root_dir = Path(root_dir)
        self.token_dir = self.root_dir / 'token_usage'
        self.token_dir.mkdir(exist_ok=True)
    
    def log_tokens(self, 
                   api_type: str,
                   tokens: int,
                   prompt_tokens: int = 0,
                   completion_tokens: int = 0,
                   context: Optional[str] = None) -> None:
        """Log token usage for an API call.
        
        Args:
            api_type: Type of API call ('digest', 'annotation', etc.)
            tokens: Total tokens used
            prompt_tokens: Tokens used for prompt
            completion_tokens: Tokens used for completion
            context: Optional context information
        """
        if tokens == 0:
            return  # Don't log zero-token calls (errors)
        
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        log_file = self.token_dir / f"{date_str}.json"
        
        # Load existing log
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {
                'date': date_str,
                'total_tokens': 0,
                'calls': []
            }
        
        # Add new entry
        entry = {
            'timestamp': now.isoformat(),
            'api_type': api_type,
            'tokens': tokens,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens
        }
        
        if context:
            entry['context'] = context
        
        log_data['calls'].append(entry)
        log_data['total_tokens'] = sum(call['tokens'] for call in log_data['calls'])
        
        # Save log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Token usage logged: {api_type} - {tokens} tokens (total today: {log_data['total_tokens']})")
    
    def get_daily_usage(self, date: datetime) -> Dict:
        """Get token usage for a specific date.
        
        Args:
            date: Date to get usage for
            
        Returns:
            Dict with usage data or empty dict if no data
        """
        date_str = date.strftime('%Y-%m-%d')
        log_file = self.token_dir / f"{date_str}.json"
        
        if not log_file.exists():
            return {
                'date': date_str,
                'total_tokens': 0,
                'by_type': {},
                'calls': []
            }
        
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        # Aggregate by type
        by_type = {}
        for call in log_data.get('calls', []):
            api_type = call['api_type']
            if api_type not in by_type:
                by_type[api_type] = 0
            by_type[api_type] += call['tokens']
        
        return {
            'date': date_str,
            'total_tokens': log_data.get('total_tokens', 0),
            'by_type': by_type,
            'calls': log_data.get('calls', [])
        }
    
    def get_summary(self, days: int = 7) -> Dict:
        """Get token usage summary for recent days.
        
        Args:
            days: Number of days to include
            
        Returns:
            Dict with summary data
        """
        from datetime import timedelta
        
        summary = []
        total_all = 0
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            usage = self.get_daily_usage(date)
            
            if usage['total_tokens'] > 0:
                summary.append({
                    'date': usage['date'],
                    'total_tokens': usage['total_tokens'],
                    'digest_tokens': usage['by_type'].get('digest', 0),
                    'annotation_tokens': usage['by_type'].get('annotation', 0)
                })
                total_all += usage['total_tokens']
        
        return {
            'days': days,
            'total_tokens': total_all,
            'daily': sorted(summary, key=lambda x: x['date'])
        }


def main():
    """Main entry point for testing."""
    from common import load_config
    
    config = load_config()
    tracker = TokenUsageTracker(config['root_dir'])
    
    # Example usage
    tracker.log_tokens('digest', 150, 100, 50, 'Overall summary')
    tracker.log_tokens('digest', 200, 150, 50, 'Category: Code')
    
    # Get today's usage
    usage = tracker.get_daily_usage(datetime.now())
    print(f"Today's usage: {usage['total_tokens']} tokens")
    print(f"By type: {usage['by_type']}")


if __name__ == "__main__":
    main()

