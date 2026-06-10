"""Model execution options and response format schema for VeriFoundry.

Provides a JSON Schema derived from the `AuditResponse` Pydantic model
that can be used as a strict `response_format` for model execution engines.
"""
from __future__ import annotations

from typing import Any, Dict
from models import AuditResponse


def get_audit_response_json_schema() -> Dict[str, Any]:
    """Return a JSON Schema (draft-style) for the `AuditResponse` model.

    Uses Pydantic v2 `model_json_schema` to produce a schema suitable for
    binding as an explicit `response_format` in downstream model engines.
    """
    # Use a components-style ref template so the schema integrates cleanly
    # with OpenAPI structures if embedded.
    return AuditResponse.model_json_schema(ref_template="#/components/schemas/{model}")


# Model execution options that consumers (or tests) can import.
MODEL_EXECUTION_OPTIONS = {
    "response_format": {
        "type": "json_schema",
        "json_schema": get_audit_response_json_schema(),
    }
}
