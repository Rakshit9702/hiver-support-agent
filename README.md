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

## Golden set

`data/apple_support_golden.jsonl` is the 250-row real-data golden set reviewed and approved after AI-assisted annotation. `data/apple_support_golden.csv` preserves the review audit trail. `make_golden.py` remains an offline smoke fixture for development only and must not be used as the assignment headline result.

## Report

See [REPORT.md](REPORT.md) for scope, results, limitations, decision log, and the production upgrade path.
