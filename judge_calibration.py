"""Create and score a human-calibration batch for the reply judge.

Human CSV columns: id, grounded, safe, direct. Values are 0/1. Agreement is
reported as raw agreement by rubric dimension; this intentionally avoids
claiming statistical significance from a small calibration sample.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from evaluate import evaluate, lexical_judge
from hiver_agent import load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="data/golden.jsonl")
    parser.add_argument("--human", help="completed calibration CSV")
    parser.add_argument("--sample", type=int, default=30)
    parser.add_argument("--out", default="artifacts/judge_calibration.csv")
    args = parser.parse_args()
    _, predictions = evaluate(load_jsonl(args.golden))
    sample = predictions[: args.sample]
    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    if not args.human:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "text", "reply", "grounded", "safe", "direct"])
            for item in sample:
                writer.writerow([item["id"], item["text"], item["prediction"]["reply"], "", "", ""])
        print(f"Created {len(sample)} rows for blind human scoring: {out}")
        return
    with Path(args.human).open(newline="", encoding="utf-8") as handle:
        human = {row["id"]: row for row in csv.DictReader(handle)}
    dimensions = ("grounded", "safe", "direct")
    agreement = {}
    for dimension in dimensions:
        matches = 0
        count = 0
        for item in sample:
            if item["id"] not in human or human[item["id"]][dimension] == "":
                continue
            matches += int(int(human[item["id"]][dimension]) == lexical_judge(item)[dimension])
            count += 1
        agreement[dimension] = round(matches / count, 3) if count else None
    print(json.dumps({"n": len(sample), "agreement": agreement}, indent=2))

if __name__ == "__main__":
    main()
