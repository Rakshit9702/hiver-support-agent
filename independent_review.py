"""Independent reviewer pass over real AppleSupport examples.

This deliberately does not read proposed_intent/proposed_escalated. It uses a
separate reviewer taxonomy and explicit text rules so results are not copied
from the agent. The output remains reviewer-draft evidence until audited.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

INTENTS = {
    "account_access": ("password", "passcode", "login", "log in", "account", "apple id", "icloud account", "disabled"),
    "billing": ("charged", "charge", "payment", "purchase", "refund", "billing", "pay", "money", "price", "£", "$"),
    "delivery": ("order", "shipped", "shipping", "delivered", "store", "warranty", "bought", "buy", "arrived"),
    "cancellation": ("cancel", "unsubscribe", "stop paying"),
    "technical_issue": ("not working", "won't", "wont", "doesn't", "doesnt", "crash", "freeze", "slow", "battery", "update", "bug", "error", "broken", "issue", "problem", "can't", "cant", "unable"),
    "product_question": ("how do", "how can", "is there", "can i", "what is", "when", "does apple", "support"),
}
RISK = ("electrocut", "overheat", "fire", "stolen", "fraud", "hack", "unsafe", "dangerous", "lawsuit", "legal", "emergency", "security", "phishing", "scam")


def review(text: str, historical_reply: str) -> tuple[str, bool, str]:
    normalized = text.lower()
    scores = {intent: sum(term in normalized for term in terms) for intent, terms in INTENTS.items()}
    intent = max(scores, key=scores.get) if max(scores.values()) else "other"
    if intent == "product_question" and scores[intent] == 1 and scores["technical_issue"]:
        intent = "technical_issue"
    risk_hit = next((term for term in RISK if term in normalized), None)
    vague = len(re.sub(r"https?://\\S+", "", normalized).split()) < 5 and not max(scores.values())
    escalated = bool(risk_hit or vague or intent == "other")
    if risk_hit:
        reason = f"Safety or security signal: {risk_hit}."
    elif vague:
        reason = "Insufficient detail to act safely."
    elif intent == "other":
        reason = "No supported intent is clear."
    else:
        reason = "Routine support issue with a concrete next step."
    return intent, escalated, reason


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/apple_support_review_pool.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/apple_support_independent_review.csv"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = ["tweet_id", "customer_text", "brand_reply", "independent_intent", "independent_escalated", "independent_reason", "review_status", "reviewer_notes"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            intent, escalated, reason = review(row["customer_text"], row["brand_reply"])
            writer.writerow({"tweet_id": row["tweet_id"], "customer_text": row["customer_text"], "brand_reply": row["brand_reply"], "independent_intent": intent, "independent_escalated": escalated, "independent_reason": reason, "review_status": "REVIEWER_DRAFT", "reviewer_notes": ""})
    print(f"Wrote {len(rows)} independent reviewer-draft labels to {args.output}")

if __name__ == "__main__":
    main()
