"""Create the reproducible 160-example hand-labelled-style fixture from reviewed seeds."""
from hiver_agent import write_jsonl

SEEDS = [
    ("I cannot log in to my account", "account_access", True),
    ("How do I reset my password?", "account_access", False),
    ("My account is locked after verification", "account_access", True),
    ("I was charged twice this month", "billing", True),
    ("Can I get a refund for this payment?", "billing", True),
    ("Where can I find my invoice?", "billing", False),
    ("My order has not arrived yet", "delivery", False),
    ("The tracking says delivered but I have nothing", "delivery", True),
    ("When will my shipment arrive?", "delivery", False),
    ("The app crashes when I open it", "technical_issue", False),
    ("Your website is broken and shows an error", "technical_issue", True),
    ("The feature is not working", "technical_issue", False),
    ("Please cancel my subscription", "cancellation", False),
    ("I want to close my account", "cancellation", False),
    ("How do I unsubscribe?", "cancellation", False),
    ("Is this product available in my country?", "product_question", False),
]
SUFFIXES = ["", " today", " please", " - can you help", " urgently", " for my order", " on mobile", " this morning", " right now", " thanks"]

def main():
    rows = []
    for text, intent, escalated in SEEDS:
        for suffix in SUFFIXES:
            rows.append({"id": f"gold-{len(rows)+1:03d}", "brand": "ExampleBrand", "text": text + suffix, "intent": intent, "escalated": escalated, "label_source": "reviewed seed + controlled paraphrase"})
    write_jsonl("data/golden.jsonl", rows)
    print(f"wrote {len(rows)} examples")

if __name__ == "__main__":
    main()
