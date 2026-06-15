---
id: investor_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted seed investor pitch deck.

Score from 0 to 1 using these criteria:

- The deck tells a coherent fundraising story from problem to ask.
- Market, traction, business model, and go-to-market claims are specific rather than generic.
- Healthcare regulatory and security concerns are handled credibly.
- The investor audience can quickly understand why this company should be funded now.
- The visual rhythm supports a live pitch and avoids dense memo-style pages.

Return JSON with `score`, `passed`, `summary`, and `details`.
