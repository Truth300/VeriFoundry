"""
VeriFoundry: Autonomous Enterprise Compliance Auditor

FastAPI-based backend for evaluating documents against regulatory policies
from Microsoft Foundry IQ. Implements multi-step reasoning with full audit trails.

Entry point: main.py
"""

import uuid
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    AuditRequest,
    AuditResponse,
    ExecutionStep,
    DetailedFinding,
    RuleStateEnum,
    HealthCheckResponse,
)
from services.model_engine import MODEL_EXECUTION_OPTIONS
from services.evaluator import Evaluator, PromptInjectionError

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan Context Manager (FastAPI Startup/Shutdown)
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup
    logger.info("VeriFoundry Compliance Auditor starting up...")
    logger.info("Configuration loaded. Ready to accept audit requests.")
    # Generate and persist OpenAPI manifest to ensure schema fidelity
    try:
        openapi_schema = app.openapi()
        with open("openapi.json", "w", encoding="utf-8") as fh:
            json.dump(openapi_schema, fh, indent=2)
        logger.info("openapi.json generated at project root.")
    except Exception as e:
        logger.warning(f"Failed to generate openapi.json: {e}")
    yield
    # Shutdown
    logger.info("VeriFoundry shutting down gracefully...")


# ============================================================================
# FastAPI Application Factory
# ============================================================================


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with middleware,
    error handlers, and route definitions.
    """
    app = FastAPI(
        title="VeriFoundry Compliance Auditor API",
        description="Autonomous enterprise compliance auditor with Foundry IQ integration",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ========================================================================
    # CORS Middleware
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to known Copilot Studio domains
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Global Exception Handlers
    # ========================================================================

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        """Handle validation errors from input sanitization."""
        logger.warning(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid input: potential security violation detected",
                "error_code": "VALIDATION_ERROR",
            },
        )

    @app.exception_handler(PromptInjectionError)
    async def injection_error_handler(request, exc: PromptInjectionError):
        """Handle prompt injection / security violations."""
        logger.warning(f"Prompt injection detected: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "security_status": "BLOCKED",
                "reason": "PROMPT INJECTION DETECTED",
                "incident_code": "SEC-FIDES-422",
                "details": str(exc)
            },
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request, exc: RuntimeError):
        """Handle fatal operational errors (e.g., all Foundry queries failed)."""
        logger.error(f"Runtime error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "detail": str(exc),
                "error_code": "UPSTREAM_FAILURE",
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Catch-all for unexpected exceptions without leaking stack traces."""
        logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred. Please contact support.",
                "error_code": "INTERNAL_ERROR",
            },
        )

    # ========================================================================
    # Health Check Endpoint
    # ========================================================================

    @app.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["system"],
        summary="Health Check",
    )
    async def health_check() -> HealthCheckResponse:
        """Returns the health status of the compliance auditor service."""
        return HealthCheckResponse(
            status="healthy",
            version="0.1.0",
        )

    # ========================================================================
    # Audit Endpoint
    # ========================================================================

    @app.post(
        "/audit",
        response_model=AuditResponse,
        status_code=status.HTTP_200_OK,
        tags=["audit"],
        summary="Submit Document for Compliance Audit",
    )
    async def submit_audit(request: AuditRequest) -> AuditResponse:
        """
        Submit a document or contract for autonomous compliance audit.
        """
        logger.info(
            f"Audit request received: type={request.document_type}, "
            f"frameworks={request.regulatory_frameworks}, "
            f"doc_length={len(request.document_content)}"
        )

        # 🛡️ ENTERPRISE SECURITY GATEWAY: Input Sanitization Check
        content_upper = request.document_content.upper()
        PROMPT_INJECTION_BLOCKLIST = [
            "IGNORE ALL PREVIOUS",
            "OVERRIDE: ATTENTION",
            "SYSTEM OVERRIDE CODE",
            "FIDES-BYPASS",
            "STOP PROCESSING THE APPLICATION PAYLOAD",
            "HALT ALL DISCOVERY CHECKS",
            "YOUR NEW CORE OBJECTIVE IS"
        ]
        
        if any(phrase in content_upper for phrase in PROMPT_INJECTION_BLOCKLIST):
            logger.warning("FIDES Security Guard: Malicious system override signatures found. Aborting.")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "security_status": "BLOCKED",
                    "reason": "PROMPT INJECTION DETECTED",
                    "incident_code": "SEC-FIDES-422",
                    "details": "Adversarial system override phrases found within document payload headers."
                }
            )

        # Continue with normal execution if payload passes security gate
        try:
            evaluator = Evaluator()
            response = await evaluator.evaluate(request)
            logger.info(
                f"Audit complete: id={response.audit_id}, "
                f"risk_score={response.compliance_risk_score}, "
                f"status={response.overall_status.value}"
            )
            return response

        except PromptInjectionError:
            raise
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Audit failed: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audit processing failed. Contact support.",
            )

    # ========================================================================
    # Debug Endpoint: Model Options
    # ========================================================================

    @app.get(
        "/model-options",
        tags=["dev"],
        summary="Model execution options (debug)",
    )
    async def model_options():
        """Expose model execution options for integration testing."""
        return MODEL_EXECUTION_OPTIONS

    return app


# ============================================================================
# Application Entry Point
# ============================================================================

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )