---
id: fundraising_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted nonprofit fundraising deck.

Score from 0 to 1 using these criteria:

- The deck balances emotional storytelling with credible impact evidence.
- The provided student, cost, graduation, and campaign facts are used accurately.
- The program model and budget use are easy for donors to understand.
- The campaign ask is specific and tied to expansion outcomes.
- Visuals and page density fit a donor meeting.

Return JSON with `score`, `passed`, `summary`, and `details`.
