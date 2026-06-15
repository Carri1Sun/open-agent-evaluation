---
id: ops_quality
type: llm_judge
weight: 0.2
threshold: 0.75
required: false
---
Evaluate the submitted manufacturing operations review deck.

Score from 0 to 1 using these criteria:

- The deck turns operating metrics into a clear performance story.
- Charts and tables highlight trends, exceptions, and line 3 downtime.
- Root causes are separated from symptoms and linked to corrective actions.
- Owners, timing, and next-month cadence are specific enough to execute.
- The presentation is dense enough for operators while still readable.

Return JSON with `score`, `passed`, `summary`, and `details`.
