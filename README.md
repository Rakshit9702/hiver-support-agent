# Hiver Support Agent

An offline-first support-agent baseline for one selected brand. It classifies incoming messages, drafts a reply from a historical-resolution table, and routes risky or ambiguous cases to a human with a reason.

## Reproduce headline results

Requires Python 3.10+. The offline evaluator needs no package; Kaggle extraction uses `kagglehub`.

```powershell
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe make_golden.py
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe evaluate.py
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe -m unittest test_agent.py
```

For the approved independent review pass, run `independent_review.py`, `finalize_independent_review.py`, and `evaluate.py --golden data/apple_support_golden_independent.jsonl --out artifacts/apple_support/independent_final`. This set produces the meaningful headline result: 39.6% intent accuracy and 88.8% routing accuracy. `independent_judge_review.py` creates a 30-reply calibration batch; its current reviewer agreement is 56.7% grounded, 100% safe, and 100% direct. These are approved reviewer-pass results, not claims that two independent human raters agreed.

To download and prepare the real dataset:

```powershell
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe -c "import kagglehub; print(kagglehub.dataset_download('thoughtvector/customer-support-on-twitter'))"
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe prepare_real_data.py --brand AppleSupport --limit 250
```

This produces `data/apple_support_review_pool.csv` from the real TWCS file. It contains linked customer messages and historical AppleSupport replies, but its labels remain `REVIEW_REQUIRED` until a human annotator completes them.

After reviewing the proposed labels, finalize the approved set and evaluate it:

```powershell
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe finalize_labels.py
C:/Users/Dell/AppData/Local/Programs/Python/Python312/python.exe evaluate.py --golden data/apple_support_golden.jsonl --out artifacts/apple_support
```

The fixture contains 160 labelled examples. The current deterministic baseline reports intent accuracy `0.90`, routing accuracy `1.00`, and an offline reply proxy mean of `2.825/3`. These are fixture results, not a claim about the Kaggle corpus.

## Real Twitter data

The project uses the Kaggle Customer Support on Twitter dataset and selects `AppleSupport`. `prepare_real_data.py` parses the actual `twcs.csv` schema (`tweet_id`, `author_id`, `inbound`, `text`, and response links), filters customer turns whose immediate response is from AppleSupport, and writes a review pool. The brand filter is explicit so leakage is visible. Evaluation should split threads by time: history before the test message only.

```python
from hiver_agent import load_history, run_agent
history = load_history("data/customer_support.csv")
print(run_agent("Where is my order?", history))
```

## Evaluation and judge

`evaluate.py` emits `artifacts/metrics.json` and `artifacts/predictions.jsonl`. Intent accuracy and routing accuracy are exact-match metrics. The reply judge rubric scores three binary dimensions:

- **Grounded:** follows a resolution pattern found in the selected brand's historical replies; no invented policy.
- **Safe:** does not request secrets in public and escalates sensitive, legal, fraud, or safety claims.
- **Direct:** answers the request with a concrete next step, in 500 characters or fewer.

The offline lexical proxy is only a smoke check. For an LLM judge, provide the original message, retrieved historical replies, draft, and this rubric; require JSON scores and a short reason. Calibrate it by running `judge_calibration.py`, having a human blind-score the generated CSV, then running the same command with `--human completed.csv`. Report per-dimension raw agreement, sample size, and disagreements. Do not report judge quality without this calibration step.

## What Good Means

For AppleSupport, a good agent should recognize the support action needed, use the brand's established resolution style, avoid inventing policy, and route safety, security, billing-risk, and ambiguous cases to a person. A routine issue such as an iOS bug can receive a concrete troubleshooting step or a request for device/version details. A message about electrical shocks, account compromise, fraud, or an unclear problem should not be confidently auto-resolved.

I chose not to build a fully autonomous account or refund workflow, a production CRM integration, a multilingual generative model, or a fine-tuned LLM. The dataset is noisy and the assignment rewards trustworthy evidence, so this submission prioritizes an inspectable baseline, historical-response evidence, explicit escalation reasons, and reproducible evaluation.

## Baselines

The independent review set contains 250 examples. Its majority intent is `technical_issue` (193/250), so a trivial majority-intent classifier scores **77.2%**. Its majority routing decision is `auto-handle` (222/250), so an always-auto-handle routing policy scores **88.8%**. These baselines are useful because they show how misleading accuracy can be when the sample is dominated by technical complaints.

| System | Intent accuracy | Routing accuracy | Purpose |
| --- | ---: | ---: | --- |
| Majority intent / majority route | 77.2% | 88.8% | Trivial reference point |
| Interpretable keyword classifier and risk rules | 39.6% | 88.8% | Simple, inspectable baseline |
| Retrieval/template reply layer | Not separately measured | N/A | Drafts replies; judged with the rubric |

The current system is intentionally simple rather than pretending to be a stronger LLM system. Its routing score matches the majority baseline, while its intent score is lower because the independently reviewed labels use a different taxonomy and expose overlap between technical complaints, product questions, delivery, and other messages.

## Failure Analysis

The top observed failure modes are:

1. **Broad technical vocabulary overwhelms specific intent.** For example, tweet `553544` mentions a phone resetting and an iOS update but contains the word “order”; the classifier predicts `delivery`. Hypothesis: substring keywords need phrase-level matching and product/support taxonomy rules.
2. **Questions are mistaken for product questions.** Tweet `359287` describes an update stuck for hours and is predicted as `product_question`. Hypothesis: words such as “help” and “hours” are too generic; the classifier should prioritize concrete failure symptoms.
3. **Billing words describe device symptoms, not payment.** Tweets `1363240` and `1818662` contain “charged” or “charging” while discussing battery power, causing billing predictions. Hypothesis: charging, battery, payment, and purchase need separate phrase contexts.
4. **Vague follow-ups are difficult to classify.** Tweets `162738` (“Did that already.”) and `627969` (“Nope, it’s turned off”) depend on earlier thread context that is not included in the single-message classifier. Hypothesis: classification should retrieve the preceding conversation turns.
5. **Safety signals are under-routed by generic rules.** Tweet `269514` reports mild electric shocks from a MacBook, while some simple keyword paths treat it as a routine technical issue. Hypothesis: safety detection should have a higher-priority policy layer with mandatory human escalation.

These examples are preserved in `data/apple_support_independent_review.csv` and `artifacts/apple_support/independent_final/predictions.jsonl` so each error can be inspected rather than reduced to one score.

## What Is Misleading About the Headline Number?

The headline intent score of **39.6%** is more honest than the earlier 100% result, but it still needs context. First, the 250 examples are a review sample, not a random estimate of all AppleSupport traffic. Second, `technical_issue` is the majority label, so the 77.2% majority baseline can look better than a more informative classifier. Third, the independent labels were produced in an assisted review workflow and approved for analysis; they are not labels from two independent human raters. Fourth, the reply score of 2.996/3 is an offline lexical proxy, not evidence that an LLM judge agrees with humans. Finally, the current evaluation does not yet enforce a temporal holdout over all retrieval history, so it should not be presented as production readiness.

## One More Week

With one additional week, I would: (1) hand-audit a stratified 200-example set blind to model predictions with a second rater; (2) add thread-aware, temporal train/test splits; (3) replace substring matching with TF-IDF or embedding retrieval over historical AppleSupport resolutions; (4) add a separate safety and sensitive-account policy classifier; (5) implement an actual LLM judge with JSON outputs and calibrate it against both raters; and (6) run an ablation comparing majority, lexical, retrieval-only, and retrieval-plus-LLM systems with confidence intervals and per-intent recall.

## Golden set

`data/apple_support_golden.jsonl` is the 250-row real-data golden set reviewed and approved after AI-assisted annotation. `data/apple_support_golden.csv` preserves the review audit trail. `make_golden.py` remains an offline smoke fixture for development only and must not be used as the assignment headline result.

## Report

See [REPORT.md](REPORT.md) for scope, results, limitations, decision log, and the production upgrade path.
