---
id: policy_quality
type: llm_judge
weight: 0.2
threshold: 0.75
required: false
---
Evaluate the submitted city mobility policy brief deck.

Score from 0 to 1 using these criteria:

- The deck is appropriate for a city council decision audience.
- Peer examples, options, impacts, and risks are connected to the recommendation.
- Equity and small-business implications are handled with specificity and balance.
- Success metrics and implementation steps are actionable.
- The deck avoids advocacy-only language and shows public-sector tradeoffs.

Return JSON with `score`, `passed`, `summary`, and `details`.
