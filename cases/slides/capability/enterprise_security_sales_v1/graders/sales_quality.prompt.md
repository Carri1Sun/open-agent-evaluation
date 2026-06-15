---
id: sales_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted enterprise security sales proposal deck.

Score from 0 to 1 using these criteria:

- The deck is tailored to a CISO buyer and uses security-relevant priorities.
- The product workflow and architecture are understandable without overloading the reader.
- ROI, proof points, and differentiators support a credible buying case.
- Compliance, risk, and rollout concerns are addressed before the close.
- The final next steps are concrete and appropriate for an enterprise deal.

Return JSON with `score`, `passed`, `summary`, and `details`.
