import re

SAFE_FALLBACK = (
    "Thanks for getting in touch — your issue has been picked up by our support "
    "team and someone will follow up with you shortly."
)

INTERNAL_TERMS = (
    "batch",
    "kb-",
    "agentforce",
    "salesforce",
    "knowledge article",
    "prior case",
    "entitlement",
    "warranty status",
    "grillmaster-reps",
)


def vet_customer_reply(text: str | None) -> tuple[str, str | None]:
    """Return (reply_to_send, reason_replaced). reason is None if the text was fine."""
    if not text or not text.strip():
        return SAFE_FALLBACK, "empty reply"

    candidate = text.strip()
    if len(candidate) > 420:
        return SAFE_FALLBACK, f"too long ({len(candidate)} chars)"
    for term in INTERNAL_TERMS:
        if term in candidate.lower():
            return SAFE_FALLBACK, f"contained internal term {term!r}"
    if candidate.count("\n") > 4 or re.search(r"^\s*[-*•]\s", candidate, re.MULTILINE):
        return SAFE_FALLBACK, "looked like a step-by-step report"

    return candidate, None
