"""Deterministic baseline and guardrails for support-ticket triage."""
from dataclasses import dataclass, asdict
import re

CATEGORIES = {
    "refund": ("refund", "return", "money back", "reimbursement"),
    "delivery": ("delivery", "shipping", "tracking", "parcel", "courier"),
    "account": ("login", "password", "account", "sign in", "locked out"),
    "product": ("broken", "defect", "damaged", "product", "item"),
}
URGENT = ("fraud", "charged twice", "double charged", "unauthorized", "account hacked", "security breach")
NEGATIVE = ("angry", "frustrated", "disappointed", "unacceptable", "broken", "missing")
ALLOWED = set(CATEGORIES) | {"other"}


@dataclass
class Decision:
    category: str
    priority: str
    sentiment: str
    confidence: float
    needs_human_review: bool
    reason: str
    draft_reply: str
    model_used: str = "rules"

    def dict(self):
        return asdict(self)


def contains(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))


def safety_gate(decision: Decision, text: str) -> Decision:
    lowered = text.lower()
    if any(contains(lowered, phrase) for phrase in URGENT):
        decision.priority = "high"
        decision.reason = "Potential security or payment issue; escalate to a human."
    decision.needs_human_review = (decision.priority == "high" or decision.confidence < 0.7
                                   or decision.category in {"refund", "account"})
    # Even a model-generated draft cannot claim a refund or factual order status.
    if decision.needs_human_review:
        decision.draft_reply = "Thank you for contacting us. We have received your request and a support specialist will review it. Please do not share passwords or payment details."
    return decision


def classify(subject: str, message: str) -> Decision:
    text = f"{subject} {message}".lower()
    scores = {category: sum(contains(text, phrase) for phrase in phrases)
              for category, phrases in CATEGORIES.items()}
    category = max(scores, key=scores.get) if max(scores.values()) else "other"
    count = scores.get(category, 0)
    confidence = min(0.9, 0.55 + 0.15 * count) if count else 0.4
    sentiment = "negative" if any(contains(text, p) for p in NEGATIVE) else "neutral"
    priority = "high" if any(contains(text, p) for p in URGENT) else "normal"
    decision = Decision(category, priority, sentiment, confidence, False,
                        f"Matched {count} {category} keyword(s)." if count else "No category keyword matched.",
                        "Thank you for contacting us. We will look into your request and get back to you.")
    return safety_gate(decision, text)


def validate_model_result(raw: dict, subject: str, message: str) -> Decision:
    """Reject malformed output; local safety rules always take precedence."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object")
    category = raw.get("category")
    priority = raw.get("priority")
    sentiment = raw.get("sentiment")
    confidence = raw.get("confidence")
    if category not in ALLOWED or priority not in {"normal", "high"} or sentiment not in {"neutral", "negative", "positive"}:
        raise ValueError("Invalid enum")
    if isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not 0 <= confidence <= 1:
        raise ValueError("Invalid confidence")
    result = Decision(category, priority, sentiment, float(confidence), False,
                      "LLM classification; local safety policy applied.",
                      "Thank you for contacting us. We will look into your request and get back to you.", "llm")
    return safety_gate(result, f"{subject} {message}")
