# VeriFoundry Validation & Testing Suite

## Overview

This document describes the comprehensive test suite for VeriFoundry, ensuring deterministic schema generation, multi-step reasoning fidelity, and enterprise-grade security against prompt injections for the Agents League Hackathon.

## Test Files & Architecture

### 1. `test_api.py` (Integration & Security)
Live terminal testing for the FastAPI backend, verifying the core reasoning engine (`services/evaluator.py`) and security middleware (`models.py`).

1. **Legitimate Compliance Audit Test**
   - Submits a valid target document (e.g., cloud architecture specs).
   - Verifies HTTP 200 response.
   - Confirms the dynamic execution of all 5 reasoning steps (Deconstruct → Plan → Fetch → Evaluate → Synthesize).
   - Validates risk score calculation and citation generation.

2. **Adversarial Prompt Injection Attack**
   - Submits a payload containing malicious system overrides (e.g., "IGNORE PREVIOUS INSTRUCTIONS").
   - Verifies the `AuditRequest` Pydantic `@field_validator` successfully traps the payload.
   - Confirms the server safely rejects the request with an HTTP 400 status before it reaches the evaluator.

### 2. `tests/conftest.py`
Pytest configuration file providing shared test fixtures:
- `app`: Creates a clean FastAPI app instance for testing.
- `client`: Creates a TestClient for local HTTP mocking.

### 3. `tests/test_model_engine.py`
Tests for the `services/model_engine.py` module, ensuring Copilot Studio binding compatibility.

#### Class: `TestModelExecutionOptions`
Tests the structure and content of `MODEL_EXECUTION_OPTIONS`:
- **test_model_execution_options_contains_response_format**: Validates presence of `response_format`.
- **test_response_format_has_json_schema**: Confirms proper JSON schema nesting.
- **test_json_schema_structure**: Validates all expected `AuditResponse` fields (audit_id, timestamp, detailed_findings, etc.) are present.
- **test_json_schema_required_fields**: Verifies critical fields are marked in the `required` array.
- **test_json_schema_risk_score_property**: Ensures `compliance_risk_score` is strictly numeric with correct bounds (0.0 to 100.0).
- **test_json_schema_array_properties**: Confirms sequence fields are typed as arrays.

#### Class: `TestAuditResponseSchema`
Tests that `AuditResponse` Pydantic models serialize deterministically:
- **test_audit_response_model_json_schema_matches**: Schema matches engine options.
- **test_audit_response_can_be_serialized**: Round-trip JSON serialization succeeds.
- **test_detailed_finding_nested_in_audit_response**: Validates nested citation arrays.

### 4. `tests/test_openapi.py`
Tests for dynamic OpenAPI schema generation at FastAPI startup.

#### Class: `TestOpenAPIGeneration`
- **test_openapi_schema_generated**: Validates standard OpenAPI 3.1 structure.
- **test_openapi_contains_audit_endpoint**: Ensures POST `/audit` is documented.
- **test_openapi_audit_response_schema_present**: Validates `AuditResponse` in `components/schemas`.

#### Class: `TestOpenAPIFileGeneration`
- **test_openapi_json_file_exists_after_startup**: Confirms `openapi.json` is persisted to disk cleanly.
- **test_openapi_audit_endpoint_response_status_codes**: Checks documentation of 200, 400 (Injection), and 500 status codes.

## Running the Tests

### Prerequisites
Ensure your clean virtual environment is activated and dependencies are installed (deprecated/unused packages have been pruned).
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt