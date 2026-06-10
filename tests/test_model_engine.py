"""Unit tests for model execution options and JSON schema generation."""
import json
import pytest
from pydantic import ValidationError

from models import AuditResponse, ExecutionStep, DetailedFinding, RuleStateEnum, ComplianceCitation
from services.model_engine import get_audit_response_json_schema, MODEL_EXECUTION_OPTIONS


class TestModelExecutionOptions:
    """Test MODEL_EXECUTION_OPTIONS schema structure."""

    def test_model_execution_options_contains_response_format(self):
        """Verify MODEL_EXECUTION_OPTIONS has required response_format key."""
        assert "response_format" in MODEL_EXECUTION_OPTIONS
        assert isinstance(MODEL_EXECUTION_OPTIONS["response_format"], dict)

    def test_response_format_has_json_schema(self):
        """Verify response_format contains json_schema key."""
        resp_fmt = MODEL_EXECUTION_OPTIONS["response_format"]
        assert "json_schema" in resp_fmt
        assert isinstance(resp_fmt["json_schema"], dict)

    def test_json_schema_structure(self):
        """Verify json_schema conforms to expected structure."""
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        # Pydantic v2 generates a schema with title, type, properties, required
        assert "properties" in schema
        assert isinstance(schema["properties"], dict)
        # Should have AuditResponse top-level properties
        expected_fields = {"audit_id", "timestamp", "compliance_risk_score", "overall_status", 
                          "detailed_findings", "execution_steps", "summary", "recommendations"}
        assert set(schema["properties"].keys()) == expected_fields

    def test_json_schema_required_fields(self):
        """Verify required fields are marked in json_schema."""
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        assert "required" in schema
        required = set(schema["required"])
        # audit_id, timestamp, compliance_risk_score, overall_status, summary are required
        assert {"audit_id", "compliance_risk_score", "overall_status", "summary"}.issubset(required)

    def test_json_schema_audit_id_property(self):
        """Verify audit_id property definition."""
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        audit_id_prop = schema["properties"]["audit_id"]
        assert audit_id_prop["type"] == "string"

    def test_json_schema_risk_score_property(self):
        """Verify compliance_risk_score property with bounds."""
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        risk_prop = schema["properties"]["compliance_risk_score"]
        assert risk_prop["type"] == "number"
        # Pydantic v2 encodes constraints as properties like minimum, maximum
        assert risk_prop.get("minimum") == 0.0 or risk_prop.get("exclusiveMinimum") == 0.0
        assert risk_prop.get("maximum") == 100.0 or risk_prop.get("exclusiveMaximum") == 100.0

    def test_json_schema_array_properties(self):
        """Verify array properties (execution_steps, detailed_findings, recommendations)."""
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        # execution_steps and detailed_findings should be arrays
        assert schema["properties"]["execution_steps"]["type"] == "array"
        assert schema["properties"]["detailed_findings"]["type"] == "array"
        assert schema["properties"]["recommendations"]["type"] == "array"


class TestAuditResponseSchema:
    """Test that AuditResponse schema matches MODEL_EXECUTION_OPTIONS."""

    def test_audit_response_model_json_schema_matches(self):
        """Verify that the schema used in MODEL_EXECUTION_OPTIONS matches AuditResponse model."""
        generated_schema = get_audit_response_json_schema()
        model_options_schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        # Both should be dictionaries with the same structure
        assert generated_schema == model_options_schema

    def test_audit_response_can_be_serialized(self):
        """Verify AuditResponse instance can be serialized to JSON matching the schema."""
        response = AuditResponse(
            audit_id="test-123",
            compliance_risk_score=25.5,
            overall_status=RuleStateEnum.COMPLIANT,
            summary="Test audit",
        )
        json_str = response.model_dump_json()
        data = json.loads(json_str)
        assert data["audit_id"] == "test-123"
        assert data["compliance_risk_score"] == 25.5
        assert data["overall_status"] == "compliant"

    def test_detailed_finding_nested_in_audit_response(self):
        """Verify DetailedFinding nesting in AuditResponse."""
        citation = ComplianceCitation(
            source_document="SOC2-1",
            quoted_text="Example quote",
            confidence_score=0.95,
        )
        finding = DetailedFinding(
            section_id="sec-1",
            rule_name="test-rule",
            rule_state=RuleStateEnum.COMPLIANT,
            reasoning="All good",
            citations=[citation],
        )
        response = AuditResponse(
            audit_id="test-456",
            compliance_risk_score=10.0,
            overall_status=RuleStateEnum.COMPLIANT,
            summary="OK",
            detailed_findings=[finding],
        )
        json_str = response.model_dump_json()
        data = json.loads(json_str)
        assert len(data["detailed_findings"]) == 1
        assert data["detailed_findings"][0]["section_id"] == "sec-1"
        assert len(data["detailed_findings"][0]["citations"]) == 1

    def test_execution_step_nested_in_audit_response(self):
        """Verify ExecutionStep nesting in AuditResponse."""
        step = ExecutionStep(
            step_number=1,
            step_name="Deconstruct",
            status="completed",
            details="Parsed document",
        )
        response = AuditResponse(
            audit_id="test-789",
            compliance_risk_score=0.0,
            overall_status=RuleStateEnum.COMPLIANT,
            summary="OK",
            execution_steps=[step],
        )
        json_str = response.model_dump_json()
        data = json.loads(json_str)
        assert len(data["execution_steps"]) == 1
        assert data["execution_steps"][0]["step_name"] == "Deconstruct"

    def test_schema_json_serializable(self):
        """Verify the schema itself is JSON serializable."""
        schema = get_audit_response_json_schema()
        json_str = json.dumps(schema)
        reloaded = json.loads(json_str)
        assert reloaded == schema
