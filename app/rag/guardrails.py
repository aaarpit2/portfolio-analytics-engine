"""
Belt-and-suspenders compliance layer. The system prompt asks the model to avoid
advisory language, but production systems shouldn't rely on prompting alone —
this does a post-generation scan and flags/raises if disallowed phrasing slips through.
"""

import re

DISALLOWED_PATTERNS = [
    r"\byou should\b",
    r"\bwe recommend\b",
    r"\bI recommend\b",
    r"\bconsider (buying|selling)\b",
    r"\byou might want to\b",
    r"\bit would be wise to\b",
    r"\bwill outperform\b",
    r"\bwill underperform\b",
    r"\bundervalued\b",
    r"\bovervalued\b",
    r"\bbuy signal\b",
    r"\bsell signal\b",
    r"\bguaranteed\b",
]

DISCLAIMER = (
    "\n\nThis is a descriptive summary of your portfolio's current composition and "
    "historical metrics. It is not investment advice or a recommendation to buy or sell "
    "any security."
)


class ComplianceViolation(Exception):
    pass


def check_compliance(text: str) -> list[str]:
    """Returns list of matched disallowed phrases, if any."""
    hits = []
    for pattern in DISALLOWED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def enforce_guardrails(text: str, strict: bool = False) -> str:
    """
    Checks generated text against disallowed patterns.
    strict=True raises on violation (fail closed); strict=False strips flagged
    sentences and appends a disclaimer (fail open with sanitization).
    Ensures the required disclaimer is present either way.
    """
    hits = check_compliance(text)

    if hits and strict:
        raise ComplianceViolation(f"Disallowed phrasing detected: {hits}")

    if hits:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        clean_sentences = [
            s for s in sentences if not any(re.search(p, s, re.IGNORECASE) for p in DISALLOWED_PATTERNS)
        ]
        text = " ".join(clean_sentences)

    if "not investment advice" not in text.lower():
        text += DISCLAIMER

    return text
