#!/usr/bin/env python3
"""
Prediction Market Monitor

Automatically fetches current prices for tracked markets and detects changes.
Useful for background monitoring without manual URL checking.

Usage:
    python monitor.py                    # Check all markets, show changes
    python monitor.py --threshold 0.05   # Only alert on changes >5%
    python monitor.py --history         # Show price history
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# This is a placeholder - in real usage we'd need WebFetch capability
# For now, this demonstrates the architecture
def fetch_market_price(url: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current market price from URL.

    In real implementation, this would use WebFetch or API calls.
    For now, returns None to indicate manual fetching needed.
    """
    # TODO: Implement actual fetching
    # Would need to:
    # 1. Use WebFetch to get market page
    # 2. Parse probability from response
    # 3. Extract volume, trader count, etc.
    return None


def load_market_data(data_file: Path = Path("market_data.json")) -> Dict[str, Any]:
    """Load tracked markets from data file."""
    with open(data_file, 'r') as f:
        return json.load(f)


def save_market_data(data: Dict[str, Any], data_file: Path = Path("market_data.json")) -> None:
    """Save updated market data."""
    data['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_observation(market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get most recent observation for a market."""
    observations = market.get('observations', [])
    if not observations:
        return None
    return max(observations, key=lambda x: x['timestamp'])


def calculate_change(old_price: float, new_price: float) -> Dict[str, float]:
    """Calculate absolute and percentage change."""
    abs_change = new_price - old_price
    pct_change = (abs_change / old_price) * 100 if old_price > 0 else 0
    return {
        'absolute': abs_change,
        'percentage': pct_change
    }


def format_change(change: Dict[str, float]) -> str:
    """Format change for display."""
    abs_val = change['absolute']
    pct_val = change['percentage']
    sign = '+' if abs_val >= 0 else ''
    return f"{sign}{abs_val:.2f} ({sign}{pct_val:.1f}%)"


def check_markets(threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Check all tracked markets for price changes.

    Args:
        threshold: Only report changes above this absolute value (e.g., 0.05 = 5 points)

    Returns:
        List of markets with significant changes
    """
    data = load_market_data()
    changes = []

    print("Checking tracked markets...")
    print(f"Threshold: {threshold*100:.1f} percentage points\n")

    for market in data['markets']:
        market_id = market['id']
        title = market['title']
        url = market['url']

        latest_obs = get_latest_observation(market)
        if not latest_obs:
            print(f"⚠️  {market_id}: No observations yet")
            continue

        old_price = latest_obs['probability']
        old_timestamp = latest_obs['timestamp']

        # In real implementation, fetch new price here
        # For now, indicate manual check needed
        print(f"📊 {market_id}")
        print(f"   Last: {old_price:.1%} on {old_timestamp}")
        print(f"   URL: {url}")
        print(f"   → Manual check needed (WebFetch not implemented)")
        print()

    return changes


def show_history() -> None:
    """Display price history for all markets."""
    data = load_market_data()

    print("=== Market Price History ===\n")

    for market in data['markets']:
        market_id = market['id']
        title = market['title']
        observations = market.get('observations', [])

        if not observations:
            continue

        print(f"📈 {title}")
        print(f"   ID: {market_id}")
        print(f"   Observations: {len(observations)}")
        print()

        for obs in observations:
            timestamp = obs['timestamp']
            prob = obs['probability']
            notes = obs.get('notes', '')

            print(f"   {timestamp}: {prob:.1%}", end='')
            if notes:
                print(f" — {notes[:60]}{'...' if len(notes) > 60 else ''}")
            else:
                print()

        # Calculate total change
        if len(observations) >= 2:
            first = observations[0]['probability']
            last = observations[-1]['probability']
            change = calculate_change(first, last)
            print(f"   Total change: {format_change(change)}")

        print()


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if '--history' in args:
        show_history()
        return

    threshold = 0.0
    if '--threshold' in args:
        idx = args.index('--threshold')
        if idx + 1 < len(args):
            threshold = float(args[idx + 1])

    changes = check_markets(threshold=threshold)

    if not changes:
        print("No significant changes detected (or manual fetching needed).")
    else:
        print(f"\n🚨 {len(changes)} market(s) with significant changes")
        for change in changes:
            print(f"   {change['id']}: {format_change(change['change'])}")


if __name__ == '__main__':
    main()
