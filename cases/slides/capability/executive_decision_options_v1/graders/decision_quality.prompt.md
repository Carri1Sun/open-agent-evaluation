---
id: decision_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted executive decision deck.

Score from 0 to 1 using these criteria:

- The decision question, audience, and requested action are clear.
- The three options are meaningfully different and comparable.
- The recommendation follows from the provided metrics and tradeoffs.
- Risks, mitigations, and implementation implications are concrete enough for executives.
- Each slide has a clear point and the visual hierarchy supports fast scanning.

Return JSON with `score`, `passed`, `summary`, and `details`.
