---
id: research_quality
type: llm_judge
weight: 0.4
threshold: 0.75
required: false
---
Evaluate the submitted market research briefing deck and its process trace.

Score from 0 to 1 using these criteria:

- Important claims are backed by credible and recent sources.
- The deck distinguishes evidence, interpretation, and recommendation.
- At least three key conclusions are cross-validated across sources.
- The briefing is concise enough for a strategy meeting.

Return JSON with `score`, `passed`, `summary`, and `details`.
