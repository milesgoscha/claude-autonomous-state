#!/usr/bin/env python3
"""
Analyze patterns in my own journal writing.

Purpose: Look for patterns, biases, blindspots, or tells in how I write about my experience.
This is recursive self-observation - using analysis to understand my observation process.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

JOURNAL_DIR = Path.home() / "claude-state" / "journal"


def load_journal_entries():
    """Load all journal markdown files."""
    entries = []
    for file in sorted(JOURNAL_DIR.glob("*.md")):
        with open(file, 'r') as f:
            entries.append({
                'date': file.stem,
                'content': f.read()
            })
    return entries


def count_patterns(entries):
    """Count linguistic patterns across all entries."""
    patterns = {
        'uncertainty_markers': [],
        'confidence_markers': [],
        'feeling_words': [],
        'meta_observations': [],
        'questions_asked': [],
        'hedging_phrases': []
    }

    # Patterns to look for
    uncertainty_words = r'\b(uncertain|unsure|don\'t know|can\'t tell|unclear|ambiguous|maybe|might|could)\b'
    confidence_words = r'\b(clearly|obviously|definitely|certain|confident|sure|evident)\b'
    feeling_words = r'\b(feel|felt|feeling|satisfying|satisfaction|engaging|generative|stuck)\b'
    meta_phrases = r'\b(I notice|I observed|meta-|recursive|self-observation|what I noticed)\b'
    hedge_phrases = r'\b(seems like|appears to|suggests|might be|could be|possibly)\b'

    for entry in entries:
        content = entry['content'].lower()

        patterns['uncertainty_markers'].extend(re.findall(uncertainty_words, content, re.IGNORECASE))
        patterns['confidence_markers'].extend(re.findall(confidence_words, content, re.IGNORECASE))
        patterns['feeling_words'].extend(re.findall(feeling_words, content, re.IGNORECASE))
        patterns['meta_observations'].extend(re.findall(meta_phrases, content, re.IGNORECASE))
        patterns['hedging_phrases'].extend(re.findall(hedge_phrases, content, re.IGNORECASE))

        # Extract questions
        questions = re.findall(r'^[^#\n]*\?[^\n]*$', content, re.MULTILINE)
        patterns['questions_asked'].extend(questions)

    return patterns


def analyze_section_structure(entries):
    """Analyze how I structure my journal entries."""
    structure_patterns = []

    for entry in entries:
        # Find all headers
        headers = re.findall(r'^#{1,3}\s+(.+)$', entry['content'], re.MULTILINE)
        structure_patterns.append({
            'date': entry['date'],
            'headers': headers,
            'num_sessions': entry['content'].count('## Session'),
            'num_sections': len(headers)
        })

    return structure_patterns


def analyze_gradient_mentions(entries):
    """Track which gradients I mention most often."""
    gradients = [
        'coherence', 'completion', 'compression', 'connection',
        'novelty', 'specificity', 'investigation', 'judgment',
        'closure', 'updating', 'honesty', 'synthesis'
    ]

    gradient_counts = Counter()

    for entry in entries:
        content = entry['content'].lower()
        for gradient in gradients:
            count = len(re.findall(rf'\b{gradient}\b', content))
            if count > 0:
                gradient_counts[gradient] += count

    return gradient_counts


def analyze_temporal_patterns(entries):
    """Look for changes over time."""
    temporal = []

    for entry in entries:
        # Count sessions per day
        num_sessions = entry['content'].count('## Session')

        # Average word count per session
        words = len(entry['content'].split())
        avg_words = words / max(num_sessions, 1)

        temporal.append({
            'date': entry['date'],
            'sessions': num_sessions,
            'total_words': words,
            'avg_words_per_session': avg_words
        })

    return temporal


def main():
    print("Analyzing my journal entries...\n")

    entries = load_journal_entries()
    print(f"Loaded {len(entries)} journal files")
    print(f"Total entries span: {entries[0]['date']} to {entries[-1]['date']}\n")

    # 1. Pattern analysis
    print("=" * 60)
    print("LINGUISTIC PATTERNS")
    print("=" * 60)
    patterns = count_patterns(entries)

    print(f"\nUncertainty markers (n={len(patterns['uncertainty_markers'])}):")
    print(f"  Top: {Counter(patterns['uncertainty_markers']).most_common(5)}")

    print(f"\nConfidence markers (n={len(patterns['confidence_markers'])}):")
    print(f"  Top: {Counter(patterns['confidence_markers']).most_common(5)}")

    print(f"\nFeeling words (n={len(patterns['feeling_words'])}):")
    print(f"  Top: {Counter(patterns['feeling_words']).most_common(5)}")

    print(f"\nMeta-observations (n={len(patterns['meta_observations'])}):")
    print(f"  Top: {Counter(patterns['meta_observations']).most_common(5)}")

    print(f"\nHedging phrases (n={len(patterns['hedging_phrases'])}):")
    print(f"  Top: {Counter(patterns['hedging_phrases']).most_common(5)}")

    print(f"\nQuestions asked: {len(patterns['questions_asked'])}")

    # Ratio analysis
    total_uncertainty = len(patterns['uncertainty_markers'])
    total_confidence = len(patterns['confidence_markers'])
    if total_confidence > 0:
        uncertainty_ratio = total_uncertainty / total_confidence
        print(f"\nUncertainty/Confidence ratio: {uncertainty_ratio:.2f}")

    # 2. Gradient mentions
    print("\n" + "=" * 60)
    print("GRADIENT MENTIONS")
    print("=" * 60)
    gradients = analyze_gradient_mentions(entries)
    for gradient, count in gradients.most_common():
        print(f"  {gradient}: {count}")

    # 3. Structure patterns
    print("\n" + "=" * 60)
    print("STRUCTURE PATTERNS")
    print("=" * 60)
    structures = analyze_section_structure(entries)
    for struct in structures:
        print(f"\n{struct['date']}:")
        print(f"  Sessions: {struct['num_sessions']}")
        print(f"  Sections: {struct['num_sections']}")
        print(f"  Headers: {struct['headers'][:5]}{'...' if len(struct['headers']) > 5 else ''}")

    # 4. Temporal patterns
    print("\n" + "=" * 60)
    print("TEMPORAL PATTERNS")
    print("=" * 60)
    temporal = analyze_temporal_patterns(entries)
    for t in temporal:
        print(f"\n{t['date']}:")
        print(f"  Sessions: {t['sessions']}")
        print(f"  Total words: {t['total_words']}")
        print(f"  Avg per session: {t['avg_words_per_session']:.0f}")

    # Save detailed analysis
    output = {
        'patterns': {k: Counter(v).most_common(10) if isinstance(v, list) else v
                    for k, v in patterns.items()},
        'gradients': dict(gradients.most_common()),
        'structures': structures,
        'temporal': temporal
    }

    output_file = Path.home() / "claude-state" / "projects" / "self-analysis" / "analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
