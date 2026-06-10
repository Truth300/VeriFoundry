"""Unit tests for OpenAPI schema generation and validation."""
import json
import pytest
from pathlib import Path


class TestOpenAPIGeneration:
    """Test openapi.json generation at FastAPI startup."""

    def test_app_has_openapi_method(self, app):
        """Verify the FastAPI app has openapi() method."""
        assert hasattr(app, "openapi")
        assert callable(app.openapi)

    def test_openapi_schema_generated(self, app):
        """Verify openapi() returns a valid OpenAPI schema dict."""
        schema = app.openapi()
        assert isinstance(schema, dict)
        assert "openapi" in schema or "swagger" in schema
        assert "paths" in schema
        assert "components" in schema or "definitions" in schema

    def test_openapi_contains_audit_endpoint(self, app):
        """Verify /audit endpoint is documented in OpenAPI schema."""
        schema = app.openapi()
        assert "/audit" in schema["paths"]
        assert "post" in schema["paths"]["/audit"]

    def test_openapi_contains_health_endpoint(self, app):
        """Verify /health endpoint is documented in OpenAPI schema."""
        schema = app.openapi()
        assert "/health" in schema["paths"]
        assert "get" in schema["paths"]["/health"]

    def test_openapi_audit_response_schema_present(self, app):
        """Verify AuditResponse schema is in components/schemas."""
        schema = app.openapi()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert "AuditResponse" in schemas or any(
            "AuditResponse" in k for k in schemas.keys()
        )

    def test_openapi_audit_request_schema_present(self, app):
        """Verify AuditRequest schema is in components/schemas."""
        schema = app.openapi()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert "AuditRequest" in schemas or any(
            "AuditRequest" in k for k in schemas.keys()
        )

    def test_openapi_response_schemas_valid(self, app):
        """Verify response schemas reference proper component definitions."""
        schema = app.openapi()
        audit_post = schema["paths"]["/audit"]["post"]
        responses = audit_post.get("responses", {})
        assert "200" in responses
        response_200 = responses["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]


class TestOpenAPIFileGeneration:
    """Test that openapi.json file is written to disk at startup."""

    def test_openapi_json_file_exists_after_startup(self, client):
        """Verify openapi.json file is created during app initialization."""
        openapi_path = Path("openapi.json")
        assert openapi_path.exists(), (
            f"openapi.json not found at {openapi_path.absolute()}. "
            f"The lifespan handler should generate it at startup."
        )

    def test_openapi_json_content_valid(self, app):
        """Verify if openapi.json exists, it contains valid JSON."""
        openapi_path = Path("openapi.json")
        if openapi_path.exists():
            with open(openapi_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            assert isinstance(content, dict)
            assert "openapi" in content or "swagger" in content
            assert "paths" in content

    def test_openapi_schema_structure(self, app):
        """Verify the generated OpenAPI schema has expected top-level structure."""
        schema = app.openapi()
        assert "paths" in schema
        assert "components" in schema

    def test_openapi_audit_endpoint_has_request_body(self, app):
        """Verify /audit POST endpoint has requestBody schema."""
        schema = app.openapi()
        audit_post = schema["paths"]["/audit"]["post"]
        assert "requestBody" in audit_post
        assert "content" in audit_post["requestBody"]

    def test_openapi_audit_endpoint_response_status_codes(self, app):
        """Verify /audit endpoint response has expected status codes."""
        schema = app.openapi()
        audit_post = schema["paths"]["/audit"]["post"]
        responses = audit_post.get("responses", {})
        assert "200" in responses
        error_codes = {"400", "422", "500", "502"}
        response_codes = set(responses.keys())
        assert len(error_codes & response_codes) > 0


class TestOpenAPISchemaConsistency:
    """Test that OpenAPI schema is consistent with Pydantic models."""

    def test_audit_response_in_openapi_matches_model(self, app):
        """Verify AuditResponse schema in OpenAPI matches the Pydantic model."""
        from models import AuditResponse

        schema = app.openapi()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        audit_response_schema = None
        for key, value in schemas.items():
            if "AuditResponse" in key:
                audit_response_schema = value
                break

        assert audit_response_schema is not None
        assert "properties" in audit_response_schema

        props = audit_response_schema["properties"]
        expected_props = {
            "audit_id", "compliance_risk_score", "overall_status",
            "summary", "execution_steps", "detailed_findings",
        }
        assert expected_props.issubset(set(props.keys()))

    def test_model_options_debug_endpoint(self, client):
        """Verify /model-options debug endpoint is accessible."""
        from services.model_engine import MODEL_EXECUTION_OPTIONS

        response = client.get("/model-options")
        assert response.status_code == 200
        data = response.json()
        assert "response_format" in data
        assert "json_schema" in data["response_format"]
