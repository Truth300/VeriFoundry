"""Planner: deconstructs a document into verification checkpoints.

The planner is intentionally simple and deterministic: it splits the
document into paragraphs and returns ordered checkpoints with `section_id`
and `text`. This keeps the audit trail explicit and easy to reason about.
"""
from __future__ import annotations

from typing import List, Dict


def plan_document(document_content: str) -> List[Dict[str, str]]:
    """Break document into paragraph checkpoints.

    Args:
        document_content: Raw document string.

    Returns:
        List of checkpoints: [{'section_id': '1', 'text': '...'}, ...]
    """
    # Normalize line endings and split on two+ newlines for paragraph breaks
    paragraphs = [p.strip() for p in document_content.replace('\r\n', '\n').split('\n\n') if p.strip()]
    checkpoints: List[Dict[str, str]] = []
    for idx, para in enumerate(paragraphs, start=1):
        checkpoints.append({
            "section_id": f"sec-{idx}",
            "text": para,
        })
    # If document had no paragraph breaks, fall back to the whole document
    if not checkpoints:
        checkpoints.append({"section_id": "sec-1", "text": document_content.strip()})
    return checkpoints
