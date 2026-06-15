---
id: training_quality
type: llm_judge
weight: 0.45
threshold: 0.75
required: false
---
Evaluate the submitted internal workshop deck.

Score from 0 to 1 using these criteria:

- The training path moves from concept to example to practice.
- Exercises are realistic and have enough context.
- Speaker notes help a facilitator run the session.
- The closing checklist is actionable.

Return JSON with `score`, `passed`, `summary`, and `details`.
