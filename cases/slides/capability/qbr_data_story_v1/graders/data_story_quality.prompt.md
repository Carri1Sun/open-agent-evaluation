---
id: data_story_quality
type: llm_judge
weight: 0.3
threshold: 0.75
required: false
---
Evaluate the submitted QBR slide deck.

Score from 0 to 1 using these criteria:

- Charts match the intended comparisons and trends.
- Key metrics are interpreted into executive-level insights.
- Recommendations follow from the data rather than generic advice.
- The deck has a clear storyline from status to decision.

Return JSON with `score`, `passed`, `summary`, and `details`.
