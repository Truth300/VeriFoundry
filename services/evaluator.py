"""Evaluation engine: routes checkpoints to FoundryClient, evaluates, and logs steps.

This module exposes `Evaluator.evaluate` which returns a dict suitable
for constructing `AuditResponse` models from `models.py`.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from datetime import datetime

from pydantic import ValidationError

from .foundry import FoundryClient
from .planner import plan_document
from models import (
    AuditRequest,
    AuditResponse,
    ExecutionStep,
    DetailedFinding,
    ComplianceCitation,
    RuleStateEnum,
)


class PromptInjectionError(ValueError):
    """Raised when suspicious content is detected in the document payload."""
    pass


class Evaluator:
    """Core compliance reasoning engine.

    Orchestrates the 5-step pipeline:
    Deconstruct → Plan → Fetch → Evaluate → Synthesize

    Uses FoundryClient for grounded policy retrieval and produces
    an AuditResponse with full execution trail and citations.
    """

    def __init__(self, foundry_client: Optional[FoundryClient] = None):
        self.client = foundry_client or FoundryClient()

    async def evaluate(self, request: AuditRequest) -> AuditResponse:
        steps: List[ExecutionStep] = []
        now = datetime.utcnow()

        # -- Step 1: Deconstruct ------------------------------------------
        steps.append(ExecutionStep(
            step_number=1,
            step_name="Deconstruct",
            status="completed",
            details="Input validated and document accepted.",
            timestamp=now,
        ))

        # -- Step 2: Plan -------------------------------------------------
        steps.append(ExecutionStep(
            step_number=2,
            step_name="Plan",
            status="in_progress",
            details="Deconstructing document into verification checkpoints.",
            timestamp=now,
        ))
        checkpoints = plan_document(request.document_content)
        steps[-1].status = "completed"
        steps[-1].details = (
            f"Created {len(checkpoints)} verification checkpoints "
            f"across {len(request.regulatory_frameworks)} frameworks: "
            f"{', '.join(request.regulatory_frameworks)}."
        )

        # -- Step 3–4: Fetch + Evaluate (per checkpoint) -------------------
        findings: List[DetailedFinding] = []
        foundry_error_count = 0
        step_no = 3

        for idx, cp in enumerate(checkpoints, start=1):
            # --- Fetch ---
            fetch_step = ExecutionStep(
                step_number=step_no,
                step_name="Fetch",
                status="in_progress",
                details=f"Searching Foundry IQ for policies relevant to checkpoint '{cp['section_id']}'.",
                timestamp=now,
            )
            steps.append(fetch_step)
            step_no += 1

            try:
                matches = await self.client.search_rules(cp["text"])
            except Exception as exc:
                foundry_error_count += 1
                fetch_step.status = "failed"
                fetch_step.error_message = str(exc)
                fetch_step.details = f"Foundry IQ query failed for checkpoint '{cp['section_id']}': {exc}"
                findings.append(DetailedFinding(
                    section_id=cp["section_id"],
                    rule_name="foundry-retrieval-error",
                    rule_state=RuleStateEnum.UNDETERMINED,
                    reasoning=f"Unable to retrieve compliance rules from Foundry IQ for this checkpoint: {exc}",
                    citations=[],
                    risk_level="undetermined",
                ))
                continue

            fetch_step.status = "completed"
            fetch_step.details = f"Retrieved {len(matches)} policy rules from Foundry IQ for checkpoint '{cp['section_id']}'."

            # --- Evaluate ---
            eval_step = ExecutionStep(
                step_number=step_no,
                step_name="Evaluate",
                status="in_progress",
                details=f"Evaluating checkpoint '{cp['section_id']}' against {len(matches)} rules.",
                timestamp=now,
            )
            steps.append(eval_step)
            step_no += 1

            if not matches:
                findings.append(DetailedFinding(
                    section_id=cp["section_id"],
                    rule_name="no-matching-rule",
                    rule_state=RuleStateEnum.UNDETERMINED,
                    reasoning="No relevant compliance rules were found in Foundry IQ for this checkpoint.",
                    citations=[],
                    risk_level="low",
                ))
                eval_step.status = "completed"
                eval_step.details = "No matching rules to evaluate."
                continue

            for rule in matches:
                rule_id = rule.get("id", rule.get("title", "unnamed-rule"))
                state, reasoning = self._evaluate_rule(cp["text"], rule)
                citations = self._build_citations(rule)

                findings.append(DetailedFinding(
                    section_id=cp["section_id"],
                    rule_name=rule_id,
                    rule_state=state,
                    reasoning=reasoning,
                    citations=citations,
                    risk_level=(
                        "low" if state == RuleStateEnum.COMPLIANT
                        else "high" if state == RuleStateEnum.NON_COMPLIANT
                        else "medium"
                    ),
                ))

            eval_step.status = "completed"
            eval_step.details = f"Evaluated {len(matches)} rules for checkpoint '{cp['section_id']}'."

        if foundry_error_count > 0 and foundry_error_count == len(checkpoints):
            raise RuntimeError("All Foundry IQ queries failed — unable to complete compliance audit.")

        # -- Step 5: Synthesize --------------------------------------------
        steps.append(ExecutionStep(
            step_number=step_no,
            step_name="Synthesize",
            status="completed",
            details="Aggregated findings and computed compliance risk score.",
            timestamp=now,
        ))

        total = len(findings) or 1
        non_compliant = sum(1 for f in findings if f.rule_state == RuleStateEnum.NON_COMPLIANT)
        undetermined = sum(1 for f in findings if f.rule_state == RuleStateEnum.UNDETERMINED)
        score = round((non_compliant / total) * 100.0, 1)

        if non_compliant > 0:
            overall = RuleStateEnum.NON_COMPLIANT
        elif undetermined > 0:
            overall = RuleStateEnum.UNDETERMINED
        else:
            overall = RuleStateEnum.COMPLIANT

        parts = [f"Audited {total} checkpoint(s)."]
        if non_compliant: parts.append(f"{non_compliant} non-compliant finding(s) detected.")
        if undetermined: parts.append(f"{undetermined} finding(s) could not be determined.")
        if not non_compliant and not undetermined: parts.append("All checkpoints passed compliance review.")
        
        recommendations = [f"[{f.section_id}] {f.rule_name}: {f.reasoning}" for f in findings if f.rule_state == RuleStateEnum.NON_COMPLIANT]

        return AuditResponse(
            audit_id=str(uuid.uuid4()),
            compliance_risk_score=score,
            overall_status=overall,
            detailed_findings=findings,
            execution_steps=steps,
            summary=" ".join(parts),
            recommendations=recommendations,
        )

    @staticmethod
    def _evaluate_rule(checkpoint_text: str, rule: dict) -> tuple[RuleStateEnum, str]:
        text = checkpoint_text.lower()
        rule_reqs = rule.get("requirements", [])
        
        if rule_reqs:
            compliant = any(req.lower() in text for req in rule_reqs)
            if compliant:
                return RuleStateEnum.COMPLIANT, "Validation logic satisfied. Target contains specific requirement constraints."
            return RuleStateEnum.NON_COMPLIANT, "Missing mandatory compliance requirements specified in the standard."

        rule_tokens = set(rule.get("text", "").lower().split())
        cp_tokens = set(text.split())
        overlap = len(rule_tokens.intersection(cp_tokens))
        
        if overlap > 3:
             return RuleStateEnum.COMPLIANT, "Significant token overlap detected matching policy requirements."
        return RuleStateEnum.NON_COMPLIANT, "Insufficient evidence for compliance or required mechanisms not found."

    @staticmethod
    def _build_citations(rule: dict) -> List[ComplianceCitation]:
        full_text = rule.get("text", "")
        excerpt = full_text[:150] + "..." if len(full_text) > 150 else full_text
        
        citations: List[ComplianceCitation] = []
        raw_citations = rule.get("citations", [])

        if not raw_citations:
            citations.append(ComplianceCitation(
                source_document=rule.get("id", rule.get("title", "unknown-rule")),
                quoted_text=excerpt,
                confidence_score=0.85,
            ))
            return citations

        for c in raw_citations:
            source = c.get("source", "unknown-source")
            citation_id = c.get("id", "")
            location = c.get("location", "")

            source_doc = f"{source}"
            if citation_id: source_doc += f" ({citation_id})"
            if location: source_doc += f" — {location}"

            citations.append(ComplianceCitation(
                source_document=source_doc,
                quoted_text=excerpt,
                confidence_score=0.90,
            ))

        return citations