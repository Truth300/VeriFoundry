#!/usr/bin/env python3
"""
Standalone test runner for VeriFoundry schema validation.
Runs without external test framework dependencies.
"""
import sys
import json
from pathlib import Path

# Add the project root to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_model_execution_options():
    """Test MODEL_EXECUTION_OPTIONS schema structure."""
    print("\n📋 Testing MODEL_EXECUTION_OPTIONS...")
    try:
        from services.model_engine import MODEL_EXECUTION_OPTIONS, get_audit_response_json_schema
        from models import AuditResponse
        
        # Test 1: Structure
        assert "response_format" in MODEL_EXECUTION_OPTIONS, "Missing response_format"
        print("  ✓ response_format key present")
        
        assert "json_schema" in MODEL_EXECUTION_OPTIONS["response_format"], "Missing json_schema"
        print("  ✓ json_schema key present")
        
        # Test 2: Schema properties
        schema = MODEL_EXECUTION_OPTIONS["response_format"]["json_schema"]
        assert "properties" in schema, "Schema missing properties"
        print("  ✓ Schema has properties")
        
        expected_fields = {
            "audit_id", "timestamp", "compliance_risk_score", "overall_status",
            "detailed_findings", "execution_steps", "summary", "recommendations"
        }
        actual_fields = set(schema["properties"].keys())
        assert expected_fields == actual_fields, f"Field mismatch: {expected_fields} vs {actual_fields}"
        print(f"  ✓ All expected fields present: {sorted(expected_fields)}")
        
        # Test 3: Required fields
        assert "required" in schema, "Schema missing required array"
        required = set(schema["required"])
        assert {"audit_id", "compliance_risk_score", "overall_status", "summary"}.issubset(required)
        print("  ✓ Required fields correctly marked")
        
        # Test 4: Risk score bounds
        risk_prop = schema["properties"]["compliance_risk_score"]
        assert risk_prop["type"] == "number", "Risk score should be number type"
        print("  ✓ compliance_risk_score is numeric type")
        
        # Test 5: Array types
        assert schema["properties"]["execution_steps"]["type"] == "array"
        assert schema["properties"]["detailed_findings"]["type"] == "array"
        assert schema["properties"]["recommendations"]["type"] == "array"
        print("  ✓ Array fields correctly typed")
        
        # Test 6: Schema JSON serializable
        json_str = json.dumps(schema)
        reloaded = json.loads(json_str)
        assert reloaded == schema
        print("  ✓ Schema is JSON serializable")
        
        print("✅ MODEL_EXECUTION_OPTIONS tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ MODEL_EXECUTION_OPTIONS tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_response_serialization():
    """Test that AuditResponse can be serialized matching the schema."""
    print("\n📋 Testing AuditResponse serialization...")
    try:
        from models import (
            AuditResponse, ExecutionStep, DetailedFinding, 
            RuleStateEnum, ComplianceCitation
        )
        import json
        
        # Test 1: Simple response
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
        print("  ✓ Simple AuditResponse serialized correctly")
        
        # Test 2: With nested DetailedFinding
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
        print("  ✓ AuditResponse with DetailedFinding serialized correctly")
        
        # Test 3: With ExecutionStep
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
        print("  ✓ AuditResponse with ExecutionStep serialized correctly")
        
        print("✅ AuditResponse serialization tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AuditResponse serialization tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openapi_schema():
    """Test OpenAPI schema generation."""
    print("\n📋 Testing OpenAPI schema generation...")
    try:
        from main import create_app
        
        app = create_app()
        schema = app.openapi()
        
        # Test 1: Basic structure
        assert isinstance(schema, dict), "OpenAPI schema should be dict"
        assert "paths" in schema, "Missing paths"
        assert "components" in schema, "Missing components"
        print("  ✓ OpenAPI schema has basic structure")
        
        # Test 2: Endpoints present
        assert "/audit" in schema["paths"], "Missing /audit endpoint"
        assert "/health" in schema["paths"], "Missing /health endpoint"
        print("  ✓ Required endpoints documented")
        
        # Test 3: Audit endpoint details
        assert "post" in schema["paths"]["/audit"], "Missing POST on /audit"
        audit_post = schema["paths"]["/audit"]["post"]
        assert "requestBody" in audit_post, "Missing requestBody"
        assert "responses" in audit_post, "Missing responses"
        print("  ✓ /audit endpoint properly documented")
        
        # Test 4: Response status codes
        responses = audit_post["responses"]
        assert "200" in responses, "Missing 200 response"
        print("  ✓ Response status codes present")
        
        # Test 5: Schemas in components
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert len(schemas) > 0, "No schemas in components"
        schema_keys = set(schemas.keys())
        # Should have AuditResponse or AuditRequest
        has_audit_response = any("AuditResponse" in k for k in schema_keys)
        has_audit_request = any("AuditRequest" in k for k in schema_keys)
        assert has_audit_response or has_audit_request, "Missing audit schemas"
        print("  ✓ Component schemas present")
        
        # Test 6: JSON serializable
        json_str = json.dumps(schema)
        reloaded = json.loads(json_str)
        assert isinstance(reloaded, dict), "OpenAPI schema should be JSON serializable"
        print("  ✓ OpenAPI schema is JSON serializable")
        
        print("✅ OpenAPI schema generation tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI schema generation tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("VeriFoundry Schema Validation Test Suite")
    print("=" * 70)
    
    results = []
    results.append(("MODEL_EXECUTION_OPTIONS", test_model_execution_options()))
    results.append(("AuditResponse Serialization", test_audit_response_serialization()))
    results.append(("OpenAPI Schema Generation", test_openapi_schema()))
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")
    
    print("=" * 70)
    print(f"Total: {passed}/{total} test groups passed")
    
    if passed == total:
        print("🎉 All validation tests PASSED!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
