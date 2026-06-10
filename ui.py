import streamlit as st
import requests
import time

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(page_title="VeriFoundry Auditor", page_icon="🛡️", layout="wide")

# Cleaned up CSS: Removed the metric background color to fix dark-mode text issues
st.markdown("""
    <style>
    .citation-block { border-left: 4px solid #4B8BBE; padding-left: 15px; color: #888; font-style: italic; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ VeriFoundry: Autonomous Enterprise Compliance Auditor")
st.caption("Agents League Hackathon 2026 — Reasoning Track Engine")

# Hardcoded Backend URL (Hidden from UI)
API_URL = "http://127.0.0.1:8000"

# ==========================================
# Sidebar Configuration
# ==========================================
with st.sidebar:
    st.header("⚙️ System Settings")
    
    framework_options = st.multiselect(
        "Target Regulatory Frameworks",
        options=["GDPR", "NIST", "SOC2", "ISO27001", "Internal Data Policy"],
        default=["GDPR", "SOC2"]
    )
    
    doc_type = st.selectbox(
        "Document Category",
        options=["contract", "technical_specification", "privacy_policy", "vendor_agreement"]
    )

# ==========================================
# Main Content Area: Input Handling
# ==========================================
doc_content = ""

tab1, tab2 = st.tabs(["📄 Upload Document", "✍️ Paste Text"])

with tab1:
    uploaded_file = st.file_uploader(
        "Upload Compliance Document", 
        type=["txt", "pdf", "docx"],
        help="Supported formats: Plain Text, PDF, or Word documents"
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        try:
            if file_extension == "txt":
                doc_content = uploaded_file.read().decode("utf-8")
            elif file_extension == "pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(uploaded_file)
                    doc_content = "".join([page.extract_text() for page in reader.pages])
                except ImportError:
                    st.error("Missing dependency: Run `pip install pypdf` to parse PDFs.")
            elif file_extension == "docx":
                try:
                    import docx
                    doc = docx.Document(uploaded_file)
                    doc_content = "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    st.error("Missing dependency: Run `pip install python-docx` to parse Word docs.")
            
            if doc_content:
                st.success(f"✅ Successfully extracted {len(doc_content)} characters from {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading file: {e}")

with tab2:
    pasted_text = st.text_area("Paste contract or architecture specs here:", height=200)
    if pasted_text:
        doc_content = pasted_text

# ==========================================
# Execution Engine
# ==========================================
st.write("---")
if st.button("🚀 Execute Autonomous Audit Loop", type="primary", use_container_width=True):
    if not doc_content:
        st.error("⚠️ Please provide document content before executing.")
    else:
        payload = {
            "document_type": doc_type,
            "document_content": doc_content,
            "regulatory_frameworks": framework_options
        }
        
        # Agentic "Thinking" Visualizer
        with st.status("🧠 Initializing Autonomous Agent Pipeline...", expanded=True) as status:
            st.write("📡 Handshaking with Microsoft Foundry IQ...")
            time.sleep(0.5) # Slight pause for visual effect during demo
            st.write("🔍 Deconstructing payload and planning queries...")
            
            try:
                # The actual backend call
                response = requests.post(f"{API_URL}/audit", json=payload)
                
                # FIDES Security Block (HTTP 422 or 400)
                if response.status_code in [400, 422]:
                    status.update(label="🚨 Security Protocol Triggered", state="error", expanded=True)
                    st.error("**PROMPT INJECTION DETECTED AND BLOCKED**")
                    st.json(response.json())
                    st.stop()
                    
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update status to complete and collapse the thinking box
                    status.update(label="✅ Autonomous Audit Complete", state="complete", expanded=False)
                    
                    # --- Dashboard Metrics ---
                    st.subheader("📊 Executive Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    risk_score = data['compliance_risk_score']
                    status_text = data['overall_status'].upper()
                    
                    delta_color = "normal" if risk_score < 50 else "inverse"
                    
                    with col1:
                        st.metric("Compliance Risk Score", f"{risk_score}%", delta=f"{risk_score}% Risk", delta_color=delta_color)
                    with col2:
                        st.metric("Overall Status", status_text)
                    with col3:
                        st.metric("Session Token ID", data['audit_id'][:8].upper())
                        
                    st.info(f"**Synthesis:** {data['summary']}")
                    
                    st.divider()
                    
                    # --- Findings & Citations ---
                    st.subheader("📝 Grounded Findings & Policy Citations")
                    for finding in data['detailed_findings']:
                        if finding['rule_state'] == "compliant":
                            icon = "✅"
                        elif finding['rule_state'] == "non_compliant":
                            icon = "❌"
                        else:
                            icon = "⚠️"
                            
                        with st.expander(f"{icon} [{finding['section_id']}] {finding['rule_name']} — Risk: {finding['risk_level'].upper()}"):
                            st.markdown(f"**Reasoning:** {finding['reasoning']}")
                            
                            st.markdown("#### 📚 Foundry IQ Citations")
                            if not finding['citations']:
                                st.write("No direct citations required (Baseline Pass).")
                            else:
                                for cit in finding['citations']:
                                    st.markdown(f"""
                                    <div class="citation-block">
                                        "{cit['quoted_text']}"<br>
                                        <small><b>Source:</b> {cit['source_document']} | <b>Confidence:</b> {cit['confidence_score']}</small>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # --- Actionable Recommendations ---
                    if data['recommendations']:
                        st.divider()
                        st.subheader("🛠️ Actionable Recommendations")
                        for rec in data['recommendations']:
                            st.warning(f"- {rec}")
                    
                    # --- Live Audit Trail ---
                    st.divider()
                    st.subheader("🔍 Backend Execution Trail")
                    with st.expander("View Multi-Step Reasoning Logs", expanded=False):
                        for step in data['execution_steps']:
                            status_icon = "🟢" if step['status'] == "completed" else "🔴" if step['status'] == "failed" else "🟡"
                            st.markdown(f"**{status_icon} Step {step['step_number']}: {step['step_name']}**")
                            st.caption(f"_{step['details']}_")
                            if step.get('error_message'):
                                st.error(step['error_message'])
                        
                else:
                    status.update(label="❌ Backend Error", state="error")
                    st.error(f"Backend Returned Error {response.status_code}")
                    st.json(response.json())
                    
            except requests.exceptions.ConnectionError:
                status.update(label="🔌 Connection Failed", state="error")
                st.error("Could not connect to FastAPI server. Ensure `uvicorn main:app` is running on port 8000.")
            except Exception as e:
                status.update(label="⚠️ Unexpected Error", state="error")
                st.error(f"An unexpected error occurred: {e}")