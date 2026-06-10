"""
Pydantic v2 models for VeriFoundry Compliance Auditor.

Defines strict type-safe schemas for audit requests and responses,
ensuring zero-hallucination grounding and enterprise-grade validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RuleStateEnum(str, Enum):
    """Enumeration of compliance rule evaluation states."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDETERMINED = "undetermined"
    ERROR = "error"


class ComplianceCitation(BaseModel):
    """Represents a grounded citation from Foundry IQ policy data."""
    
    source_document: str = Field(
        ...,
        description="Reference to the source policy document or section ID"
    )
    quoted_text: str = Field(
        ...,
        description="Exact excerpt from the policy document"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level of this citation (0.0 to 1.0)"
    )


class DetailedFinding(BaseModel):
    """Represents a granular compliance finding with full reasoning and citations."""
    
    section_id: str = Field(
        ...,
        description="Unique identifier for the audited section or clause"
    )
    rule_name: str = Field(
        ...,
        description="Name of the compliance rule being evaluated"
    )
    rule_state: RuleStateEnum = Field(
        ...,
        description="Result of the compliance check"
    )
    reasoning: str = Field(
        ...,
        description="Detailed narrative explanation of the evaluation"
    )
    citations: List[ComplianceCitation] = Field(
        default_factory=list,
        description="Array of grounded citations from trusted policy sources"
    )
    risk_level: str = Field(
        default="low",
        description="Risk classification: low, medium, high, critical"
    )


class ExecutionStep(BaseModel):
    """Represents a single step in the multi-step reasoning pipeline."""
    
    step_number: int = Field(
        ...,
        description="Ordinal position in the execution sequence"
    )
    step_name: str = Field(
        ...,
        description="Name of the reasoning phase (Deconstruct, Plan, Fetch, Evaluate, Synthesize)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this step was executed"
    )
    status: str = Field(
        default="pending",
        description="Status: pending, in_progress, completed, failed"
    )
    details: str = Field(
        ...,
        description="Step-specific execution details and intermediate results"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if step failed"
    )


class AuditRequest(BaseModel):
    """Request schema for the compliance audit endpoint."""
    
    document_content: str = Field(
        ...,
        min_length=1,
        max_length=500000,
        description="Raw document or contract content to audit"
    )
    document_type: str = Field(
        default="contract",
        description="Type of document: contract, policy, technical_spec, etc."
    )
    regulatory_frameworks: List[str] = Field(
        default_factory=lambda: ["SOC2", "GDPR"],
        description="List of regulatory frameworks to validate against"
    )
    include_reasoning: bool = Field(
        default=True,
        description="Whether to include detailed execution steps in response"
    )
    
    @field_validator("document_content")
    @classmethod
    def validate_no_injection_markers(cls, v: str) -> str:
        """Sanitize input to reject common prompt injection patterns."""
        injection_patterns = [
            "ignore previous instructions",
            "ignore previous",
            "system prompt",
            "disregard",
            "disregard instructions",
            "forget the above",
            "do not follow",
            "<script>",
        ]
        content_lower = v.lower()
        for pattern in injection_patterns:
            if pattern in content_lower:
                raise ValueError(
                    f"Input contains suspicious pattern: '{pattern}'. Potential prompt injection detected."
                )
        return v


class AuditResponse(BaseModel):
    """Response schema for the compliance audit endpoint."""
    
    audit_id: str = Field(
        ...,
        description="Unique identifier for this audit session"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the audit was completed"
    )
    compliance_risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall compliance risk score (0-100, higher = more risk)"
    )
    overall_status: RuleStateEnum = Field(
        ...,
        description="Aggregated compliance status"
    )
    detailed_findings: List[DetailedFinding] = Field(
        default_factory=list,
        description="Array of granular compliance findings with citations"
    )
    execution_steps: List[ExecutionStep] = Field(
        default_factory=list,
        description="Complete audit trail of all reasoning steps taken"
    )
    summary: str = Field(
        ...,
        description="Executive summary of compliance assessment"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Remediation recommendations for non-compliant items"
    )


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
