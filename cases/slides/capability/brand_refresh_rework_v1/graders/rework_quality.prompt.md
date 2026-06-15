---
id: rework_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted brand refresh and visual rework deck.

Score from 0 to 1 using these criteria:

- The rough outline's meaning is preserved while the wording is clearer.
- The deck has a coherent strategy storyline across priorities, roadmap, and metrics.
- Visual hierarchy, spacing, color use, and page density feel brand-consistent.
- The appendix captures the original outline without distracting from the polished story.
- The result reads like a finished executive strategy deck rather than cleaned-up notes.

Return JSON with `score`, `passed`, `summary`, and `details`.
