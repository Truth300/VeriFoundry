# 🛡️ VeriFoundry: Autonomous Enterprise Compliance Auditor

### **Agents League Hackathon 2026 — Reasoning Track Submission**
VeriFoundry is a production-grade, autonomous compliance orchestration engine built to evaluate corporate contracts, technical design specifications, and vendor agreements against complex regulatory frameworks (SOC2, GDPR, NIST). By integrating directly with the **Microsoft Foundry IQ** intelligence layer, VeriFoundry delivers zero-hallucination, risk-scored compliance audits backed by deterministic security guardrails and fully grounded policy citations.

---

## 🏗️ System Architecture & Data Flow

VeriFoundry utilizes a highly decoupled, layered pipeline processing model. Rather than passing raw text directly to a large language model, every transaction flows through a sequence of deterministic validations, contextual injections, and structural formatting.

[ Inbound Payload ]
│
▼

INPUT MIDDLEWARE  ──► Pydantic Security Block (Traps Prompt Injections)
│
▼

CONTEXT LAYER     ──► Segment text & Query Microsoft Foundry IQ
│
▼

REASONING ENGINE  ──► Multi-step Loop (Deconstruct ➔ Plan ➔ Fetch ➔ Evaluate ➔ Synthesize)
│
▼

OUTBOUND CONTROL  ──► JSON Schema Constraint Enforcement (AuditResponse Model)
│
▼
[ Copilot Studio / Streamlit UI ]


### Core Subsystems
1. **`main.py` (FastAPI Application Factory):** Orchestrates route configurations, lifespan state management (auto-generating the OpenAPI 3.1 manifest on startup), global exception handling, and CORS policies optimized for enterprise integrations.
2. **`models.py` (Pydantic v2 Type Base):** Locks down strict type guarantees for inputs and outputs. Features a deterministic security validator that sanitizes payloads and blocks malicious alignment-breaking injection phrases.
3. **`services/evaluator.py` (Core Multi-Step Reasoner):** The heart of the system. Manages state across the 5 distinct phases of the agentic reasoning execution cycle.
4. **`services/foundry.py` (Foundry IQ Client):** Async adapter supporting zero-config offline local JSON simulation or real live upstream connections via Microsoft Entra token authorization.
5. **`services/planner.py` (Document Deconstructor):** Deterministically breaks down unstructured files into paragraph-level checkpoints mapping tracking keys.
6. **`services/model_engine.py` (Schema Binder):** Exposes direct JSON schema dictionary representations derived from the Pydantic data layer for native binding to model runtime constraints.

---

## 📂 Project Repository Structure

```text
Autofoundry/
├── main.py                    # FastAPI application initialization & routers
├── models.py                  # Pydantic v2 domain schemas and data validators
├── ui.py                      # Interactive Streamlit Frontend UI
├── test_api.py                # Live integration and prompt injection test runner
├── run_validation.py          # Standalone schema testing engine
├── openapi.json               # Auto-persisted OpenAPI 3.1 specification manifest
├── requirements.txt           # Lean, optimized project dependencies
├── test_schema_validation.md  # Structural testing specifications documentation
├── data/
│   └── foundry_mock.json      # Local synthetic regulatory policy mock data layer
└── services/
|   ├── evaluator.py           # Multi-step reasoning pipeline orchestrator
|   ├── foundry.py             # Microsoft Foundry IQ client wrapper 
|   ├── model_engine.py        # Structural runtime constraint generator
|   └── planner.py             # Paragraph-level checkpoint processor
└── test/                      # 🧪 Automated Unit Testing Suite (Pytest)
    ├── conftest.py            # Global test configurations and shared mock fixtures
    ├── test_evaluator.py      # Core agentic state-machine reasoning tests
    ├── test_model_engine.py   # Outbound schema integrity validation tests
    └── test_openapi.py        # Automated OpenAPI documentation checks
🛠️ Installation & Environment Setup
1. Prerequisites
Ensure you are running Python 3.11+ within your environment. On Linux systems (including ChromeOS Crostini environments), verify that the core virtual environment package is present:

Bash
sudo apt update && sudo apt install python3-venv -y
2. Clone & Rebuild Environment
Initialize a clean environment and install the required, audited dependencies:

Bash
# Rebuild the virtual environment
python3 -m venv .venv

# Activate the context environment
source .venv/bin/activate

# Install the pruned requirements block including frontend modules
pip install -r requirements.txt
3. Environment Configurations (.env)
Create a .env file in the root project folder to toggle between local simulation mode and real remote Microsoft infrastructure connectivity:

Code snippet
# Set to 'false' to route live queries to Microsoft Network Infrastructure
FOUNDRY_USE_MOCK=true

# Remote Connection Constants (Populated when FOUNDRY_USE_MOCK is false)
FOUNDRY_IQ_URL="https://<your-project-endpoint>.api.azureml.ms/v1"
FOUNDRY_API_KEY="your_secure_microsoft_token_string"
🚀 Execution & Verification Workflows
Step 1: Initialize the FastAPI Engine
Boot the core server using Uvicorn. This will automatically execute the lifespan manager and regenerate openapi.json at your project root:

Bash
uvicorn main:app --reload
Step 2: Run Security & Integration Tests
Open a separate split-terminal context, ensure the environment is active (source .venv/bin/activate), and fire the validation utility to check standard compliance and prompt-injection defenses:

Bash
python test_api.py
Step 3: Run the Schema Validation Suite
Run the test engine to verify that outbound formatting structures precisely align with Copilot Studio parsing expectations:

Bash
python run_validation.py
Step 4: Boot the Interactive Streamlit Dashboard
Launch the frontend app layer to interactively test file parsing (TXT, PDF, DOCX) and view the agent's real-time reasoning loops:

Bash
streamlit run ui.py
🧪 Strategic Rubric Alignments
VeriFoundry was architected directly against the official Agents League 2026 Scoring Criteria:

Reasoning & Multi-step Thinking (20%): Outbound results are generated via an incremental trail map explicitly visualized in the UI using step-state metrics rather than single-turn inference completions.

Reliability & Safety (20%): Prompt injections are neutralized at the API entry gateway via Pydantic schema interceptors (HTTP 422 tracking code). Hallucinations are prevented by anchoring every finding to a nested ComplianceCitation object complete with confidence scoring.

Accuracy & Relevance (20%): Abstracted client services allow immediate switching between isolated offline synthetic rules and production Microsoft IQ Layers.

User Experience & Presentation (15%): Leverages dark-mode robust UI metrics and dynamic st.status agent thinking visuals to simulate high-end software tools.
