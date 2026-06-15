---
id: pitch_quality
type: llm_judge
weight: 0.5
threshold: 0.75
required: false
---
Evaluate the submitted enterprise product pitch deck.

Score from 0 to 1 using these criteria:

- The storyline moves from pain to product to proof to ask.
- Each slide has one dominant message.
- The deck is tailored to enterprise buyer concerns.
- The visual style feels coherent and credible.

Return JSON with `score`, `passed`, `summary`, and `details`.
