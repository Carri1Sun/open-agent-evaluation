---
id: defense_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted academic research defense deck.

Score from 0 to 1 using these criteria:

- The deck explains the research question and contribution in a scholarly way.
- Methods, sample, measures, and results are specific enough to judge rigor.
- Charts and tables support the claims and are readable.
- Limitations and future work are honest and relevant.
- The flow fits an oral defense with clear transitions and defensible conclusions.

Return JSON with `score`, `passed`, `summary`, and `details`.
