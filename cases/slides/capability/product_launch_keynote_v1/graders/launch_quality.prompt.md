---
id: launch_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted product launch keynote deck.

Score from 0 to 1 using these criteria:

- The first slides create a clear product reveal and audience hook.
- The product, features, demo flow, pricing, and call to action are easy to follow.
- The deck feels suitable for a live keynote with strong visual pacing.
- The copy is concise and avoids overexplaining product mechanics.
- The presentation leaves the audience with a memorable product position.

Return JSON with `score`, `passed`, `summary`, and `details`.
