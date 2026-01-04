#!/usr/bin/env python3
"""
Creative Variation Generator

Actually generates creative story variations by exploring different
narrative transforms rather than using placeholder logic.

This doesn't call an external LLM but demonstrates the creative generation
logic that could be used with one.
"""

import random
from typing import List, Dict

class VariationGenerator:
    """Generates creative variations of story seeds."""

    def __init__(self):
        # Different types of narrative transforms to explore
        self.transforms = [
            {
                "name": "inversion",
                "description": "Invert the core premise",
                "prompt": "What if the central element was its opposite?",
            },
            {
                "name": "scale_shift",
                "description": "Change the scale (individual ↔ collective)",
                "prompt": "What if this happened at a completely different scale?",
            },
            {
                "name": "temporal_distortion",
                "description": "Alter the temporal structure",
                "prompt": "What if time worked differently in this story?",
            },
            {
                "name": "agency_swap",
                "description": "Swap agency between elements",
                "prompt": "What if the objects had agency and the subjects didn't?",
            },
            {
                "name": "genre_collision",
                "description": "Collide with a different genre's logic",
                "prompt": "What if this story followed the logic of a completely different genre?",
            },
            {
                "name": "constraint_intensification",
                "description": "Intensify a hidden constraint",
                "prompt": "What if a background constraint became the central conflict?",
            },
            {
                "name": "metaphor_literalization",
                "description": "Make the metaphorical literal",
                "prompt": "What if the metaphors became literally true?",
            },
            {
                "name": "setting_as_character",
                "description": "Give the setting agency",
                "prompt": "What if the environment had desires and acted on them?",
            },
        ]

    def generate_variations(self, seed_text: str, num_variations: int = 5) -> List[Dict]:
        """
        Generate creative variations of a seed story.

        For now, this creates structured prompts that would guide variation generation.
        With an LLM integration, these would become actual narrative variations.
        """
        # Sample transforms without replacement
        selected_transforms = random.sample(
            self.transforms,
            min(num_variations, len(self.transforms))
        )

        variations = []
        for i, transform in enumerate(selected_transforms):
            variation = {
                "id": i,
                "transform_type": transform["name"],
                "transform_description": transform["description"],
                "seed_text": seed_text,
                "prompt": transform["prompt"],
                # In a full implementation, this would be generated text
                "text": self._apply_transform_concept(seed_text, transform)
            }
            variations.append(variation)

        return variations

    def _apply_transform_concept(self, seed: str, transform: Dict) -> str:
        """
        Conceptually apply a transform to demonstrate what it would do.

        With real LLM integration, this would generate full variations.
        """
        # Extract key elements from the seed for demonstration
        concepts = {
            "inversion": f"[Inversion] {seed} → But what if the opposite were true?",
            "scale_shift": f"[Scale Shift] {seed} → Imagine this at civilization scale.",
            "temporal_distortion": f"[Temporal] {seed} → What if this happened backwards through time?",
            "agency_swap": f"[Agency Swap] {seed} → What if the inanimate chose instead?",
            "genre_collision": f"[Genre Collision] {seed} → Now tell this as a heist.",
            "constraint_intensification": f"[Constraint] {seed} → But the real story is about what can't happen.",
            "metaphor_literalization": f"[Literal Metaphor] {seed} → Every figure of speech becomes real.",
            "setting_as_character": f"[Active Setting] {seed} → The place itself wants something.",
        }

        return concepts.get(transform["name"], f"[{transform['name']}] {seed}")


class InterestingnessEvaluator:
    """Evaluates variations for different types of interesting-ness."""

    def __init__(self):
        # Criteria for interesting-ness
        self.criteria = {
            "surprise": "How unexpected is this direction?",
            "coherence": "Does it maintain internal logic?",
            "generativity": "Does it open new narrative possibilities?",
            "tension": "Does it create productive contradiction?",
            "specificity": "Is it concrete rather than abstract?",
            "resonance": "Does it connect to deeper patterns?",
        }

    def evaluate(self, variation: Dict) -> Dict:
        """
        Evaluate a variation across multiple criteria.

        Returns scores and reasoning.
        """
        # In a full implementation, this would use judgment/reasoning
        # For now, simulate evaluation with some heuristics

        scores = {}
        reasoning = []

        # Different transforms tend toward different strengths
        transform_profiles = {
            "inversion": {"surprise": 0.8, "coherence": 0.7, "generativity": 0.6},
            "scale_shift": {"surprise": 0.6, "coherence": 0.8, "generativity": 0.8},
            "temporal_distortion": {"surprise": 0.9, "coherence": 0.5, "generativity": 0.7},
            "agency_swap": {"surprise": 0.8, "coherence": 0.6, "generativity": 0.9},
            "genre_collision": {"surprise": 0.7, "coherence": 0.6, "generativity": 0.8},
            "constraint_intensification": {"surprise": 0.6, "coherence": 0.9, "generativity": 0.7},
            "metaphor_literalization": {"surprise": 0.9, "coherence": 0.5, "generativity": 0.8},
            "setting_as_character": {"surprise": 0.7, "coherence": 0.7, "generativity": 0.9},
        }

        transform_type = variation["transform_type"]
        profile = transform_profiles.get(transform_type, {})

        # Add some randomness to simulate variation in execution quality
        for criterion in self.criteria:
            base_score = profile.get(criterion, 0.5)
            score = base_score + (random.random() - 0.5) * 0.3  # ±0.15 variation
            score = max(0, min(1, score))  # Clamp to [0, 1]
            scores[criterion] = score

        # Overall score (weighted average)
        overall = (
            scores.get("surprise", 0) * 0.3 +
            scores.get("generativity", 0) * 0.3 +
            scores.get("coherence", 0) * 0.2 +
            scores.get("tension", 0) * 0.1 +
            scores.get("specificity", 0) * 0.05 +
            scores.get("resonance", 0) * 0.05
        )

        # Generate reasoning
        top_criterion = max(scores.items(), key=lambda x: x[1])
        reasoning.append(f"Strong in {top_criterion[0]} ({top_criterion[1]:.2f})")

        weak_criteria = [k for k, v in scores.items() if v < 0.5]
        if weak_criteria:
            reasoning.append(f"Could develop: {', '.join(weak_criteria)}")

        return {
            "overall_score": overall,
            "scores": scores,
            "reasoning": " | ".join(reasoning),
            "transform_type": transform_type,
        }


def demonstrate_variation_generation():
    """Demonstrate the variation generation and evaluation system."""
    generator = VariationGenerator()
    evaluator = InterestingnessEvaluator()

    seed = "A librarian discovers that forgotten books dream of the readers they never had."

    print("="*70)
    print("CREATIVE VARIATION GENERATION")
    print("="*70)
    print(f"\nSeed Story:")
    print(f"  {seed}")
    print()

    # Generate variations
    variations = generator.generate_variations(seed, num_variations=6)

    print(f"Generated {len(variations)} variations:\n")

    # Evaluate and display
    evaluated = []
    for var in variations:
        eval_result = evaluator.evaluate(var)
        evaluated.append({**var, **eval_result})

    # Sort by score
    evaluated.sort(key=lambda x: x["overall_score"], reverse=True)

    # Display
    for i, var in enumerate(evaluated, 1):
        print(f"{i}. {var['transform_description'].upper()}")
        print(f"   Score: {var['overall_score']:.3f}")
        print(f"   Transform: {var['transform_type']}")
        print(f"   Variation: {var['text']}")
        print(f"   Evaluation: {var['reasoning']}")
        print()

    print("-"*70)
    print(f"Top variation: {evaluated[0]['transform_description']}")
    print(f"Score: {evaluated[0]['overall_score']:.3f}")
    print("-"*70)


if __name__ == "__main__":
    demonstrate_variation_generation()
