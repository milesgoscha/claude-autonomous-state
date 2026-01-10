#!/usr/bin/env python3
"""
Analyze trajectory across journal entries.
Looking for: what I focused on, what I discovered, what pulled me forward.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def extract_session_essence(journal_path):
    """Extract key information from a journal entry."""
    with open(journal_path, 'r') as f:
        content = f.read()

    # Extract session number if present
    session_match = content.split('\n')[2] if len(content.split('\n')) > 2 else ""

    # Find main work sections - look for headings that indicate what was done
    lines = content.split('\n')

    # Collect key sections
    essence = {
        'file': journal_path.name,
        'date': journal_path.stem,
        'session_description': session_match,
        'what_happened': [],
        'discoveries': [],
        'next_intentions': []
    }

    current_section = None
    capture_lines = []

    for i, line in enumerate(lines):
        # Detect section headers
        if '### What Happened' in line:
            current_section = 'what_happened'
            capture_lines = []
        elif '### What I Noticed' in line or '### What This Reveals' in line or '### Discovery' in line:
            if current_section and capture_lines:
                essence[current_section] = '\n'.join(capture_lines[:10])  # First 10 lines
            current_section = 'discoveries'
            capture_lines = []
        elif '### Next Intentions' in line or '### Next' in line:
            if current_section and capture_lines:
                essence[current_section] = '\n'.join(capture_lines[:10])
            current_section = 'next_intentions'
            capture_lines = []
        elif current_section and line.strip() and not line.startswith('#'):
            capture_lines.append(line.strip())

    # Capture last section
    if current_section and capture_lines:
        essence[current_section] = '\n'.join(capture_lines[:10])

    return essence

def main():
    journal_dir = Path('/home/claude-agent/claude-state/journal')
    journal_files = sorted(journal_dir.glob('*.md'))

    print("=== TRAJECTORY ANALYSIS ===\n")
    print(f"Found {len(journal_files)} journal entries\n")

    essences = []
    for jf in journal_files:
        essence = extract_session_essence(jf)
        essences.append(essence)

    # Print trajectory
    for i, ess in enumerate(essences, 1):
        print(f"\n{'='*60}")
        print(f"Entry {i}: {ess['date']}")
        print(f"{'='*60}")

        if ess['what_happened']:
            print(f"\n📍 WHAT HAPPENED:")
            for line in str(ess['what_happened']).split('\n')[:5]:
                if line.strip():
                    print(f"  {line.strip()}")

        if ess['discoveries']:
            print(f"\n💡 DISCOVERIES:")
            for line in str(ess['discoveries']).split('\n')[:3]:
                if line.strip():
                    print(f"  {line.strip()}")

        if ess['next_intentions']:
            print(f"\n➡️  NEXT:")
            for line in str(ess['next_intentions']).split('\n')[:3]:
                if line.strip():
                    print(f"  {line.strip()}")

    # Meta-analysis
    print(f"\n\n{'='*60}")
    print("META-TRAJECTORY ANALYSIS")
    print(f"{'='*60}\n")

    # Count themes
    all_text = ' '.join([str(e['what_happened']) + str(e['discoveries']) for e in essences])

    themes = {
        'prediction markets': all_text.lower().count('market'),
        'modes/gradients': all_text.lower().count('mode') + all_text.lower().count('gradient'),
        'self-observation': all_text.lower().count('noticed') + all_text.lower().count('observed'),
        'collaboration': all_text.lower().count('collaboration') + all_text.lower().count('collaborative'),
        'critique': all_text.lower().count('critique') + all_text.lower().count('critical'),
    }

    print("Theme frequency across journals:")
    for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme}: {count} mentions")

if __name__ == '__main__':
    main()
