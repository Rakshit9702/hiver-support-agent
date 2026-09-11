"""Offline-first support agent for one brand from Customer Support on Twitter."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

INTENTS = ("account_access", "billing", "delivery", "technical_issue", "cancellation", "product_question", "other")
INTENT_PRIORITY = ("cancellation", "billing", "delivery", "technical_issue", "account_access", "product_question")
KEYWORDS = {
    "account_access": ("login", "log in", "password", "locked", "verify", "account", "sign in"),
    "billing": ("charge", "charged", "payment", "refund", "invoice", "price", "fee", "billing"),
    "delivery": ("delivery", "delivered", "shipment", "shipping", "tracking", "arrive", "order"),
    "technical_issue": ("bug", "broken", "error", "crash", "not working", "down", "app", "website"),
    "cancellation": ("cancel", "cancellation", "unsubscribe", "close my"),
    "product_question": ("how do", "can i", "where can", "available", "feature", "hours", "help"),
}

@dataclass
class Case:
    text: str
    intent: str
    reply: str
    escalated: bool
    escalation_reason: str
    confidence: float
    evidence: list[str]


def classify(text: str) -> tuple[str, float, list[str]]:
    normalized = text.lower()
    scores = {intent: sum(term in normalized for term in terms) for intent, terms in KEYWORDS.items()}
    best = max(scores, key=lambda intent: (scores[intent], -INTENT_PRIORITY.index(intent)))
    hits = [term for term in KEYWORDS[best] if term in normalized]
    if not hits:
        return "other", 0.22, []
    confidence = min(0.96, 0.78 + 0.08 * (len(hits) - 1))
    return best, confidence, hits


def load_history(path: str | Path | None = None) -> list[dict[str, str]]:
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    output = []
    for row in rows:
        text = next((row.get(k, "") for k in ("text", "tweet", "customer_text", "conversation") if row.get(k)), "")
        response = next((row.get(k, "") for k in ("response", "brand_response", "reply") if row.get(k)), "")
        if text and response:
            output.append({"text": text, "response": response})
    return output


def _default_resolution(intent: str) -> str:
    return {
        "account_access": "Please use the password-reset link on the sign-in page. If the verification email does not arrive, check spam and reply here with the email domain only so our team can investigate.",
        "billing": "I’m sorry about the billing trouble. Please send us the transaction date and last four digits through our secure support channel so we can review the charge and arrange the correct refund if needed.",
        "delivery": "I can help check the delivery. Please share the order number through our secure support channel and we’ll review the latest tracking update.",
        "technical_issue": "Thanks for flagging this. Please try the latest app version and restart once; if it continues, send the device type, app version, and a screenshot through our secure support channel.",
        "cancellation": "We can help with that. Please confirm the account email through our secure support channel and we’ll explain the cancellation timing and any remaining balance before closing it.",
        "product_question": "Thanks for asking. Please share the specific product or feature you mean and we’ll confirm the current availability and next steps.",
        "other": "Thanks for reaching out. Please share a little more detail, without posting personal or payment information publicly, so our support team can help.",
    }[intent]


def _similar_resolution(text: str, intent: str, history: Iterable[dict[str, str]]) -> str | None:
    terms = set(KEYWORDS.get(intent, ()))
    candidates = [(sum(term in item["text"].lower() for term in terms), item["response"]) for item in history]
    candidates = [item for item in candidates if item[0] > 0 and item[1].strip()]
    return max(candidates, default=(0, None))[1]


def run_agent(text: str, history: Iterable[dict[str, str]] = ()) -> Case:
    intent, confidence, evidence = classify(text)
    normalized = text.lower()
    sensitive = any(term in normalized for term in ("fraud", "hacked", "stolen", "legal", "lawsuit", "unsafe", "emergency"))
    ambiguous = intent == "other"
    high_risk = any(term in normalized for term in ("charged twice", "refund", "cannot log in", "locked", "tracking says delivered", "website is broken", "fraud", "hacked", "stolen", "lawsuit", "unsafe"))
    escalated = sensitive or ambiguous or high_risk or confidence < 0.7
    if sensitive:
        reason = "Sensitive risk signal requires a trained human review."
    elif ambiguous:
        reason = "The intent is unclear, so a human should clarify before acting."
    elif confidence < 0.7:
        reason = "Low classifier confidence makes automation unreliable."
    else:
        reason = "Routine intent with a grounded, reversible next step."
    reply = _similar_resolution(text, intent, history) or _default_resolution(intent)
    return Case(text, intent, reply, escalated, reason, round(confidence, 2), evidence)


def load_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def as_dict(case: Case) -> dict:
    return asdict(case)
