---
id: compliance_quality
type: llm_judge
weight: 0.35
threshold: 0.75
required: false
---
Evaluate the submitted healthcare compliance training deck.

Score from 0 to 1 using these criteria:

- The learning path moves from objectives to concepts, scenarios, practice, and recap.
- Allowed and prohibited data use are explained in operational language.
- Exercises and quiz questions test realistic judgment rather than recall only.
- Speaker notes give a facilitator enough support to run the session.
- The deck is clear, professional, and cautious about regulated data handling.

Return JSON with `score`, `passed`, `summary`, and `details`.
