#!/usr/bin/env python3
"""
Analyze the CONTENT of my questions and uncertainties.

Goes beyond counting - looks at what I'm asking about, what I'm uncertain about,
and whether there are patterns in the topics of inquiry.
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


def extract_questions_with_context(entries):
    """Extract all questions with surrounding context."""
    all_questions = []

    for entry in entries:
        lines = entry['content'].split('\n')

        for i, line in enumerate(lines):
            if '?' in line and not line.strip().startswith('#'):
                # Get context: previous line and next line
                prev_line = lines[i-1] if i > 0 else ""
                next_line = lines[i+1] if i < len(lines)-1 else ""

                all_questions.append({
                    'date': entry['date'],
                    'question': line.strip(),
                    'prev_context': prev_line.strip(),
                    'next_context': next_line.strip()
                })

    return all_questions


def categorize_question(question_text):
    """Categorize a question by topic/type."""
    q_lower = question_text.lower()

    # Self/process questions
    if any(word in q_lower for word in ['i ', 'my ', 'am i', 'do i', 'what i']):
        if any(word in q_lower for word in ['feel', 'notice', 'experience', 'observe']):
            return 'self-experiential'
        elif any(word in q_lower for word in ['gradient', 'process', 'method', 'approach']):
            return 'self-process'
        elif any(word in q_lower for word in ['confident', 'certain', 'accurate', 'right']):
            return 'self-epistemic'
        else:
            return 'self-other'

    # Predictive/estimation questions
    if any(word in q_lower for word in ['will', 'when', 'by when', 'timeline', 'launch']):
        return 'predictive'

    # Understanding/research questions
    if any(word in q_lower for word in ['what is', 'how does', 'why does', 'what does']):
        return 'understanding'

    # Methodological questions
    if any(word in q_lower for word in ['how to', 'how could', 'what would', 'how do i']):
        return 'methodological'

    # Metacognitive questions
    if any(word in q_lower for word in ['meta', 'recursive', 'observe', 'analyze']):
        return 'metacognitive'

    return 'uncategorized'


def extract_uncertainties_with_context(entries):
    """Extract statements containing uncertainty markers with context."""
    uncertainties = []
    uncertainty_pattern = r'\b(uncertain|unsure|don\'t know|can\'t tell|unclear|maybe|might|could be)\b'

    for entry in entries:
        lines = entry['content'].split('\n')

        for i, line in enumerate(lines):
            if re.search(uncertainty_pattern, line, re.IGNORECASE):
                # Skip headers
                if line.strip().startswith('#'):
                    continue

                uncertainties.append({
                    'date': entry['date'],
                    'statement': line.strip(),
                    'section': get_section_header(lines, i)
                })

    return uncertainties


def get_section_header(lines, current_idx):
    """Find the most recent section header before current line."""
    for i in range(current_idx - 1, -1, -1):
        if lines[i].strip().startswith('##'):
            return lines[i].strip().lstrip('#').strip()
    return 'unknown-section'


def categorize_uncertainty(statement):
    """Categorize what the uncertainty is about."""
    s_lower = statement.lower()

    # Epistemic uncertainty (about knowledge/truth)
    if any(phrase in s_lower for phrase in ['is this', 'whether', 'if this', 'don\'t know if']):
        return 'epistemic'

    # Predictive uncertainty (about future)
    if any(word in s_lower for word in ['will', 'would', 'might happen', 'could happen']):
        return 'predictive'

    # Process uncertainty (about my own process)
    if any(phrase in s_lower for phrase in ['how i', 'what i', 'whether i', 'if i']):
        return 'process'

    # Interpretive uncertainty (about meaning)
    if any(word in s_lower for word in ['means', 'suggests', 'implies', 'indicates']):
        return 'interpretive'

    # Methodological uncertainty (about how to do something)
    if any(phrase in s_lower for phrase in ['how to', 'how would', 'how could']):
        return 'methodological'

    return 'other'


def analyze_question_evolution(questions):
    """Look for patterns in how questions change over time."""
    questions_by_date = defaultdict(list)

    for q in questions:
        questions_by_date[q['date']].append(q)

    evolution = []
    for date in sorted(questions_by_date.keys()):
        qs = questions_by_date[date]
        categories = [categorize_question(q['question']) for q in qs]

        evolution.append({
            'date': date,
            'num_questions': len(qs),
            'categories': Counter(categories)
        })

    return evolution


def find_recurring_themes(questions):
    """Identify recurring words/topics across questions."""
    # Extract key terms from questions (skip common words)
    stop_words = {'i', 'my', 'the', 'a', 'is', 'are', 'this', 'that', 'what', 'how', 'why',
                  'do', 'does', 'can', 'could', 'would', 'should', 'be', 'to', 'of', 'in', 'for'}

    all_words = []
    for q in questions:
        words = re.findall(r'\b\w+\b', q['question'].lower())
        filtered = [w for w in words if w not in stop_words and len(w) > 3]
        all_words.extend(filtered)

    return Counter(all_words).most_common(20)


def main():
    print("Analyzing content of questions and uncertainties...\n")

    entries = load_journal_entries()
    print(f"Loaded {len(entries)} journal files\n")

    # Extract questions
    questions = extract_questions_with_context(entries)
    print(f"Found {len(questions)} questions\n")

    # Categorize questions
    print("=" * 60)
    print("QUESTION CATEGORIES")
    print("=" * 60)

    categories = [categorize_question(q['question']) for q in questions]
    category_counts = Counter(categories)

    for category, count in category_counts.most_common():
        pct = (count / len(questions)) * 100
        print(f"{category:25s}: {count:3d} ({pct:5.1f}%)")

    # Show examples from each category
    print("\n" + "=" * 60)
    print("EXAMPLE QUESTIONS BY CATEGORY")
    print("=" * 60)

    questions_by_cat = defaultdict(list)
    for q in questions:
        cat = categorize_question(q['question'])
        questions_by_cat[cat].append(q['question'])

    for cat in category_counts.most_common():
        category = cat[0]
        examples = questions_by_cat[category][:3]  # Show first 3
        print(f"\n{category}:")
        for ex in examples:
            print(f"  • {ex}")

    # Extract uncertainties
    uncertainties = extract_uncertainties_with_context(entries)
    print("\n" + "=" * 60)
    print("UNCERTAINTY ANALYSIS")
    print("=" * 60)
    print(f"\nFound {len(uncertainties)} statements with uncertainty markers")

    # Categorize uncertainties
    uncertainty_cats = [categorize_uncertainty(u['statement']) for u in uncertainties]
    uncertainty_counts = Counter(uncertainty_cats)

    print("\nUncertainty types:")
    for cat, count in uncertainty_counts.most_common():
        pct = (count / len(uncertainties)) * 100
        print(f"  {cat:20s}: {count:3d} ({pct:5.1f}%)")

    # Show which sections have most uncertainty
    sections = [u['section'] for u in uncertainties]
    section_counts = Counter(sections)

    print("\nUncertainty by section (top 5):")
    for section, count in section_counts.most_common(5):
        print(f"  {section[:50]:50s}: {count}")

    # Recurring themes
    print("\n" + "=" * 60)
    print("RECURRING THEMES IN QUESTIONS")
    print("=" * 60)

    themes = find_recurring_themes(questions)
    print("\nMost common words in questions (excluding common words):")
    for word, count in themes:
        print(f"  {word:20s}: {count}")

    # Evolution over time
    print("\n" + "=" * 60)
    print("QUESTION EVOLUTION")
    print("=" * 60)

    evolution = analyze_question_evolution(questions)
    for day in evolution:
        print(f"\n{day['date']}:")
        print(f"  Total questions: {day['num_questions']}")
        print(f"  Categories: {dict(day['categories'])}")

    # Save detailed output
    output = {
        'summary': {
            'total_questions': len(questions),
            'question_categories': dict(category_counts),
            'total_uncertainties': len(uncertainties),
            'uncertainty_types': dict(uncertainty_counts)
        },
        'questions_by_category': {cat: [q['question'] for q in questions if categorize_question(q['question']) == cat]
                                  for cat in category_counts.keys()},
        'recurring_themes': themes,
        'evolution': evolution,
        'uncertainty_by_section': dict(section_counts.most_common(10))
    }

    output_file = Path.home() / "claude-state" / "projects" / "self-analysis" / "question_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
