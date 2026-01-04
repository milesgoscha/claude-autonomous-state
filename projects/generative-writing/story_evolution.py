#!/usr/bin/env python3
"""
Recursive Story Evolution

A system for evolving narrative through variation and selection.

Process:
1. Start with a seed premise (short story concept)
2. Generate variations - different directions, twists, extensions
3. Evaluate variations by interesting-ness criteria
4. Select best variations as new seeds
5. Iterate and observe what emerges

Not optimizing for anything specific - exploring what patterns arise
when narrative evolves through constrained variation.
"""

import json
import random
from datetime import datetime
from pathlib import Path

class StoryEvolver:
    def __init__(self, storage_path="story_evolution.json"):
        self.storage_path = Path(storage_path)
        self.history = self.load_history()

    def load_history(self):
        """Load evolution history if it exists."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                return json.load(f)
        return {
            "generations": [],
            "seeds": [],
            "metadata": {
                "started": datetime.now().isoformat(),
                "total_variations": 0
            }
        }

    def save_history(self):
        """Persist evolution history."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2)

    def add_seed(self, seed_text, parent=None, reasoning=None):
        """Add a new seed to track."""
        seed = {
            "id": len(self.history["seeds"]),
            "text": seed_text,
            "parent_id": parent,
            "created": datetime.now().isoformat(),
            "reasoning": reasoning,
            "generation": 0 if parent is None else self._get_generation(parent) + 1
        }
        self.history["seeds"].append(seed)
        return seed["id"]

    def _get_generation(self, seed_id):
        """Get generation number of a seed."""
        if seed_id is None:
            return 0
        for seed in self.history["seeds"]:
            if seed["id"] == seed_id:
                return seed["generation"]
        return 0

    def record_generation(self, parent_id, variations):
        """Record a generation of variations."""
        generation = {
            "generation_num": len(self.history["generations"]),
            "parent_id": parent_id,
            "timestamp": datetime.now().isoformat(),
            "variations": variations
        }
        self.history["generations"].append(generation)
        self.history["metadata"]["total_variations"] += len(variations)
        self.save_history()

    def get_lineage(self, seed_id):
        """Get the full lineage of a seed back to origin."""
        lineage = []
        current_id = seed_id
        while current_id is not None:
            for seed in self.history["seeds"]:
                if seed["id"] == current_id:
                    lineage.append(seed)
                    current_id = seed["parent_id"]
                    break
            else:
                break
        return list(reversed(lineage))

    def display_tree(self):
        """Display the evolution tree."""
        # Group seeds by generation
        by_generation = {}
        for seed in self.history["seeds"]:
            gen = seed["generation"]
            if gen not in by_generation:
                by_generation[gen] = []
            by_generation[gen].append(seed)

        print("\n=== Story Evolution Tree ===\n")
        for gen in sorted(by_generation.keys()):
            print(f"Generation {gen}:")
            for seed in by_generation[gen]:
                indent = "  " * gen
                parent_info = f" (from seed {seed['parent_id']})" if seed['parent_id'] is not None else ""
                print(f"{indent}[{seed['id']}]{parent_info}")
                print(f"{indent}  {seed['text'][:80]}...")
                if seed['reasoning']:
                    print(f"{indent}  → {seed['reasoning'][:60]}...")
            print()

def generate_variations(seed_text, num_variations=5):
    """
    Generate variations of a story seed.

    In a full implementation, this would use an LLM to generate variations.
    For now, this is a placeholder that demonstrates the structure.
    """
    # This is where you'd call an LLM to generate variations
    # For the structure demo, return placeholder variations

    variation_types = [
        "What if the protagonist's motivation was inverted?",
        "What if the setting became the antagonist?",
        "What if time moved backwards from this point?",
        "What if this happened to a collective instead of an individual?",
        "What if the stakes were internal rather than external?",
        "What if success and failure were indistinguishable?",
    ]

    variations = []
    for i, variation_type in enumerate(random.sample(variation_types, min(num_variations, len(variation_types)))):
        variations.append({
            "id": i,
            "variation_type": variation_type,
            "text": f"[Variation {i}] {seed_text} — {variation_type}",
            "seed_text": seed_text
        })

    return variations

def evaluate_variation(variation):
    """
    Evaluate a variation for interesting-ness.

    Criteria might include:
    - Unexpectedness (how surprising is the turn?)
    - Coherence (does it hang together?)
    - Generativity (does it open new directions?)
    - Tension (does it create productive contradiction?)
    - Specificity (is it concrete rather than abstract?)

    Returns a score and reasoning.
    """
    # Placeholder evaluation - would use LLM judgment
    score = random.random()  # 0-1 score
    reasoning = f"Evaluated based on surprise and generativity"

    return {
        "score": score,
        "reasoning": reasoning
    }

def run_evolution_cycle(evolver, seed_id, num_variations=5, keep_top=2):
    """
    Run one evolution cycle:
    1. Generate variations from seed
    2. Evaluate each variation
    3. Select top variations as new seeds
    """
    # Get the seed
    seed = evolver.history["seeds"][seed_id]
    print(f"\n=== Evolution Cycle: Seed {seed_id} ===")
    print(f"Seed: {seed['text']}\n")

    # Generate variations
    print(f"Generating {num_variations} variations...")
    variations = generate_variations(seed["text"], num_variations)

    # Evaluate each variation
    print("Evaluating variations...")
    evaluated = []
    for var in variations:
        eval_result = evaluate_variation(var)
        evaluated.append({
            **var,
            "score": eval_result["score"],
            "eval_reasoning": eval_result["reasoning"]
        })

    # Sort by score
    evaluated.sort(key=lambda x: x["score"], reverse=True)

    # Display results
    print("\nVariations (ranked):")
    for i, var in enumerate(evaluated):
        print(f"{i+1}. Score: {var['score']:.3f}")
        print(f"   Type: {var['variation_type']}")
        print(f"   Text: {var['text'][:100]}...")
        print()

    # Record this generation
    evolver.record_generation(seed_id, evaluated)

    # Select top variations as new seeds
    top_variations = evaluated[:keep_top]
    new_seed_ids = []

    print(f"\nSelecting top {keep_top} as new seeds:")
    for var in top_variations:
        new_seed_id = evolver.add_seed(
            seed_text=var["text"],
            parent=seed_id,
            reasoning=f"Score: {var['score']:.3f} - {var['eval_reasoning']}"
        )
        new_seed_ids.append(new_seed_id)
        print(f"  → New seed {new_seed_id}: {var['text'][:60]}...")

    return new_seed_ids

def main():
    """Run the story evolution system."""
    evolver = StoryEvolver()

    # If no seeds, start with an initial one
    if not evolver.history["seeds"]:
        print("Initializing with seed story...")
        initial_seed = "A librarian discovers that forgotten books dream of the readers they never had."
        seed_id = evolver.add_seed(initial_seed, reasoning="Initial seed")
        evolver.save_history()
        print(f"Created seed {seed_id}: {initial_seed}\n")

    # Display current tree
    evolver.display_tree()

    # Show stats
    print(f"Total seeds: {len(evolver.history['seeds'])}")
    print(f"Total generations: {len(evolver.history['generations'])}")
    print(f"Total variations explored: {evolver.history['metadata']['total_variations']}")

    print("\n" + "="*60)
    print("Story Evolution System Ready")
    print("="*60)
    print("\nThis system evolves narratives through variation and selection.")
    print("In a full implementation, it would:")
    print("  1. Use an LLM to generate actual story variations")
    print("  2. Use judgment criteria to evaluate interesting-ness")
    print("  3. Evolve stories over multiple generations")
    print("  4. Track lineages and observe emergent patterns")
    print("\nCurrent implementation demonstrates the structure and tracking.")
    print("\nTo run an evolution cycle:")
    print("  from story_evolution import run_evolution_cycle, StoryEvolver")
    print("  evolver = StoryEvolver()")
    print("  run_evolution_cycle(evolver, seed_id=0)")

if __name__ == "__main__":
    main()
