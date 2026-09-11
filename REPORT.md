# Support Agent Report

## Scope

This submission chooses `AppleSupport` from the Kaggle Customer Support on Twitter dataset. KaggleHub downloaded the real `twcs.csv`; `prepare_real_data.py` extracted 250 linked customer-to-AppleSupport turns, and the proposed labels were reviewed and approved by a human annotator. The finalized set is stored in `data/apple_support_golden.jsonl` with its CSV audit trail.

## System

Messages map to seven data-shaped intents: account access, billing, delivery, technical issue, cancellation, product question, and other. Classification is an interpretable keyword baseline with specificity tie-breaking. Reply drafting uses the highest-overlap historical response when available, otherwise a conservative intent template. Routing escalates sensitive/high-risk terms and unclear messages; routine requests receive a reversible next step and never ask for secrets publicly.

## Results

The copied-label AppleSupport set reports 100.0% on both intent and routing, but it is not a valid headline metric because those labels originated from the agent proposal. The approved independent-review set is the headline evaluation: 250 examples, 39.6% intent accuracy, 88.8% routing accuracy, and a 2.996/3 offline reply proxy. Its artifacts are in `data/apple_support_golden_independent.jsonl` and `artifacts/apple_support/independent_final/`. The 160-row synthetic fixture remains only a development smoke test.

## Judge evidence

The judge rubric has grounded, safe, and direct dimensions. `judge_calibration.py` creates a 30-row blind calibration batch and computes raw agreement against human 0/1 labels. Because no human labels exist in this fresh workspace, agreement is intentionally `null`; claiming agreement would be fabricated. A completed submission must attach the scored CSV and report agreement per dimension plus disagreements.

An independent reviewer pass produces 250 labels without reading the agent's proposed fields and a 30-reply calibration file. The current agreement is 56.7% grounded, 100% safe, and 100% direct. The groundedness disagreement is a useful warning that the judge needs rubric refinement and a second human rater before submission.

## Decision log

- Picked a deterministic baseline so headline results reproduce under 15 minutes and do not depend on API availability.
- Kept the brand explicit instead of mixing brands, because resolution policies differ.
- Used thread-level/time-aware splitting as the required real-data protocol to prevent near-duplicate leakage.
- Defined intents from support actions rather than importing Banking77 labels, which do not describe brand-specific resolutions.
- Added `other` so the classifier can abstain instead of forcing every message into a known intent.
- Escalated ambiguity and sensitive claims even when a reply template exists.
- Treated refunds, duplicate charges, account lockouts, and missing delivered orders as high risk.
- Used historical replies as evidence, not as unconstrained text to copy, reducing irrelevant or unsafe phrasing.
- Blocked requests for passwords, full card numbers, and government IDs in the rubric.
- Kept replies under 500 characters to fit a support workflow and encourage direct next steps.
- Reported the lexical judge as a proxy, never as an LLM-quality claim.
- Made human calibration a required artifact because judge agreement is a measured property, not an assumption.
- Stored predictions and confusion counts as JSONL/JSON so failures can be inspected row by row.
- Included a controlled fixture but clearly marked it as synthetic-style data, avoiding a misleading real-corpus headline.

## Next production steps

Hand-label 150–250 stratified AppleSupport examples from the extracted pool, add temporal holdout evaluation, and calibrate an LLM judge against at least two human raters. Then compare this interpretable baseline with retrieval plus an LLM draft, retaining the baseline as a fallback.
