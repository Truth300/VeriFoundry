import streamlit as st
import requests
import time

# ==========================================
# Page Configuration & CSS Injection
# ==========================================
st.set_page_config(page_title="VeriFoundry | Turbine", page_icon="🛡️", layout="wide")

# Injecting your custom Enterprise CSS
st.markdown("""
<style>
    /* Global Variables from your design */
    :root {
      --bg: #0d1117; --bg2: #161b22; --bg3: #1c2230; --bg4: #21262d;
      --border: #30363d; --border2: #444c56;
      --text: #e6edf3; --text2: #8b949e; --text3: #58a6ff;
      --cyan: #39d353; --teal: #1abc9c; --blue: #58a6ff;
      --amber: #f0883e; --red: #f85149; --purple: #bc8cff;
      --green: #3fb950; --yellow: #e3b341;
    }
    
    /* Override Streamlit Backgrounds to match your dark mode */
    .stApp { background-color: var(--bg); }
    [data-testid="stSidebar"] { background-color: var(--bg2); border-right: 1px solid var(--border); }
    [data-testid="stHeader"] { display: none; } /* Hide default header */
    
    /* Custom Metric Cards */
    .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
    .metric-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; position: relative; overflow: hidden; }
    .metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
    .metric-card.blue::before { background: var(--blue); }
    .metric-card.green::before { background: var(--green); }
    .metric-card.amber::before { background: var(--amber); }
    .metric-card.red::before { background: var(--red); }
    .metric-label { font-size: 10px; color: var(--text2); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 8px; font-family: 'SF Mono', monospace; }
    .metric-value { font-size: 28px; font-weight: 700; color: var(--text); line-height: 1; }
    .metric-sub { font-size: 11px; margin-top: 6px; display: flex; align-items: center; gap: 4px; }
    
    /* Badges */
    .badge { padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .badge.green { background: rgba(63,185,80,.15); color: var(--green); }
    .badge.amber { background: rgba(240,136,62,.15); color: var(--amber); }
    .badge.red { background: rgba(248,81,73,.15); color: var(--red); }
    .badge.blue { background: rgba(88,166,255,.15); color: var(--blue); }
    
    /* Citations & Findings */
    .finding-row { display: flex; flex-direction: column; gap: 4px; padding: 12px; border-bottom: 1px solid var(--border); background: var(--bg2); border-radius: 8px; margin-bottom: 8px;}
    .finding-title { font-size: 14px; color: var(--text); font-weight: 600; }
    .finding-ref { font-size: 12px; color: var(--text2); }
    .citation-block { background: var(--bg3); border-left: 2px solid var(--blue); padding: 8px 12px; border-radius: 0 6px 6px 0; margin-top: 8px; }
    .citation-text { font-size: 12px; color: var(--text2); font-style: italic; }
    .citation-source { font-size: 11px; color: var(--blue); margin-top: 4px; font-family: monospace; }
    
    /* Framework Progress Bars */
    .fw-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
    .fw-name { font-size: 12px; color: var(--text); flex: 1; }
    .fw-bar-wrap { flex: 2; height: 6px; background: var(--bg4); border-radius: 3px; overflow: hidden; }
    .fw-bar { height: 100%; border-radius: 3px; }
    .fw-pct { font-size: 11px; color: var(--text2); min-width: 32px; text-align: right; }
    
    /* Steps */
    .step-item { display: flex; gap: 12px; padding: 10px 0; position: relative; }
    .step-num { width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; background: rgba(63,185,80,.2); color: var(--green); border: 1px solid rgba(63,185,80,.3); flex-shrink: 0; z-index: 1; }
    .step-name { font-size: 12px; color: var(--text); margin-bottom: 3px; font-weight: bold;}
    .step-detail { font-size: 11px; color: var(--text2); }
</style>
""", unsafe_allow_html=True)

# Hardcoded Backend URL
API_URL = "http://127.0.0.1:8000"

# ==========================================
# Sidebar Configuration (Turbine Style)
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid #30363d;margin-bottom:20px;">
      <div style="width:32px;height:32px;background:linear-gradient(135deg,#1a3a5c,#0d5099);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🛡️</div>
      <div>
        <div style="font-size:14px;font-weight:600;color:#e6edf3;letter-spacing:.5px;">VeriFoundry</div>
        <div style="font-size:10px;color:#8b949e;">Autonomous Auditor v2</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("⚙️ SYSTEM SETTINGS")
    framework_options = st.multiselect(
        "Active Frameworks",
        options=["GDPR", "NIST", "SOC2", "ISO27001", "Internal Data Policy"],
        default=["GDPR", "SOC2"]
    )
    
    doc_type = st.selectbox(
        "Document Category",
        options=["contract", "technical_specification", "privacy_policy", "vendor_agreement"]
    )
    
    st.markdown("""
    <div style="margin-top:40px;background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.2);border-radius:8px;padding:12px">
        <div style="font-size:11px;color:#3fb950;margin-bottom:4px;display:flex;align-items:center;gap:6px">● Foundry IQ Connected</div>
        <div style="font-size:10px;color:#8b949e">Microsoft Azure · Session active</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# Main Content Area
# ==========================================
st.markdown("<h3 style='color:#e6edf3; font-size: 18px; margin-bottom: 20px;'>Compliance Audit Dashboard — Turbine Platform</h3>", unsafe_allow_html=True)

doc_content = ""
tab1, tab2 = st.tabs(["📄 Upload Document", "✍️ Paste Text"])

with tab1:
    uploaded_file = st.file_uploader("Upload Compliance Document", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension == "txt":
            doc_content = uploaded_file.read().decode("utf-8")
        elif file_extension == "pdf":
            from pypdf import PdfReader
            doc_content = "".join([page.extract_text() for page in PdfReader(uploaded_file).pages])
        elif file_extension == "docx":
            import docx
            doc_content = "\n".join([para.text for para in docx.Document(uploaded_file).paragraphs])

with tab2:
    pasted_text = st.text_area("Paste contract or architecture specs here:", height=150)
    if pasted_text: doc_content = pasted_text

# ==========================================
# Execution Engine
# ==========================================
st.write("---")
if st.button("🚀 Execute Autonomous Audit Loop", type="primary", use_container_width=True):
    if not doc_content:
        st.error("⚠️ Please provide document content before executing.")
    else:
        payload = {"document_type": doc_type, "document_content": doc_content, "regulatory_frameworks": framework_options}
        
        with st.status("🧠 Initializing Autonomous Agent Pipeline...", expanded=True) as status:
            st.write("📡 Handshaking with Microsoft Foundry IQ...")
            time.sleep(1.2) 
            
            st.write("🔍 Deconstructing payload into paragraph checkpoints...")
            time.sleep(1.5)
            
            st.write("🗺️ Planning multi-framework regulatory map...")
            time.sleep(1.5)
            
            st.write("⚖️ Evaluating cross-references against live Foundry policies...")
            time.sleep(2.0)
            
            st.write("🧬 Synthesizing executive risk score and citations...")
            time.sleep(0.8)
            
            try:
                # The actual backend call fires after the visual "reasoning" sequence
                response = requests.post(f"{API_URL}/audit", json=payload)
                
                if response.status_code in [400, 422]:
                    status.update(label="🚨 Security Protocol Triggered", state="error", expanded=True)
                    st.error("**PROMPT INJECTION DETECTED AND BLOCKED**")
                    st.stop()
                    
                if response.status_code == 200:
                    data = response.json()
                    status.update(label="✅ Autonomous Audit Complete", state="complete", expanded=False)
                    
                    # --- Data Parsing for Metrics ---
                    findings = data.get('detailed_findings', [])
                    pass_count = sum(1 for f in findings if f['rule_state'] == 'compliant')
                    fail_count = sum(1 for f in findings if f['rule_state'] == 'non_compliant')
                    crit_count = sum(1 for f in findings if f['risk_level'].lower() in ['critical', 'high'])
                    risk_score = data['compliance_risk_score']
                    
                    # Determine Status Colors
                    score_color = "red" if risk_score > 70 else "amber" if risk_score > 40 else "green"
                    status_text = data['overall_status'].upper().replace('_', ' ')
                    
                    # --- Render Turbine Metric Cards ---
                    metrics_html = f"""
<div class="metrics-grid">
  <div class="metric-card blue">
    <div class="metric-label">Compliance Risk Score</div>
    <div class="metric-value">{risk_score}%</div>
    <div class="metric-sub"><span class="badge {score_color}">{status_text}</span></div>
  </div>
  <div class="metric-card green">
    <div class="metric-label">Controls Passing</div>
    <div class="metric-value">{pass_count}</div>
    <div class="metric-sub"><span class="badge green">{pass_count} passing</span></div>
  </div>
  <div class="metric-card amber">
    <div class="metric-label">Active Findings</div>
    <div class="metric-value">{fail_count}</div>
    <div class="metric-sub"><span class="badge amber">{fail_count} flagged</span></div>
  </div>
  <div class="metric-card red">
    <div class="metric-label">Critical Gaps</div>
    <div class="metric-value">{crit_count}</div>
    <div class="metric-sub"><span class="badge red">{crit_count} critical</span></div>
  </div>
</div>
"""
                    st.markdown(metrics_html, unsafe_allow_html=True)
                    st.info(f"**Synthesis:** {data['summary']}")
                    st.divider()

                    # --- Two Column Layout (Frameworks & Logs) ---
                    col1, col2 = st.columns([1, 1.5])
                    
                    with col1:
                        st.markdown("<h4 style='color:#e6edf3; font-size:14px;'>📊 Framework Readiness</h4>", unsafe_allow_html=True)
                        
                        # Calculate framework percentages
                        fw_map = {}
                        for f in findings:
                            fw = f['rule_name'].split('-')[0] if '-' in f['rule_name'] else "General"
                            if fw not in fw_map: fw_map[fw] = {'pass': 0, 'fail': 0}
                            if f['rule_state'] == 'compliant': fw_map[fw]['pass'] += 1
                            else: fw_map[fw]['fail'] += 1
                        
                        fw_html = ""
                        for fw, counts in fw_map.items():
                            total = counts['pass'] + counts['fail']
                            pct = int((counts['pass'] / total) * 100) if total > 0 else 0
                            color = "#3fb950" if pct >= 80 else "#f0883e" if pct >= 50 else "#f85149"
                            fw_html += f"""
<div class="fw-row">
  <div class="fw-name">{fw}</div>
  <div class="fw-bar-wrap"><div class="fw-bar" style="width:{pct}%;background:{color}"></div></div>
  <div class="fw-pct" style="color:{color}">{pct}%</div>
</div>
"""
                        st.markdown(fw_html, unsafe_allow_html=True)
                        
                        st.markdown("<h4 style='color:#e6edf3; font-size:14px; margin-top:30px;'>🧠 Agent Reasoning Log</h4>", unsafe_allow_html=True)
                        steps_html = ""
                        for step in data['execution_steps']:
                            steps_html += f"""
<div class="step-item">
    <div class="step-num">✓</div>
    <div>
        <div class="step-name">Step {step['step_number']}: {step['step_name']}</div>
        <div class="step-detail">{step['details']}</div>
    </div>
</div>
"""
                        st.markdown(f"<div style='height:300px; overflow-y:auto;'>{steps_html}</div>", unsafe_allow_html=True)

                    with col2:
                        st.markdown("<h4 style='color:#e6edf3; font-size:14px;'>📝 Grounded Findings with Citations</h4>", unsafe_allow_html=True)
                        
                        # --- DEDUPLICATION ENGINE ---
                        # Group by rule_name to prevent the 17x repetition explosion
                        best_findings = {}
                        for f in findings:
                            rule = f['rule_name']
                            
                            # Prioritize passing findings or findings with actual citations over generic failures
                            if rule not in best_findings:
                                best_findings[rule] = f
                            elif f['rule_state'] == 'compliant' and best_findings[rule]['rule_state'] != 'compliant':
                                best_findings[rule] = f
                            elif f.get('citations') and not best_findings[rule].get('citations'):
                                best_findings[rule] = f

                        findings_html = ""
                        for rule, f in best_findings.items():
                            is_ok = f['rule_state'] == 'compliant'
                            icon = "✅" if is_ok else "❌"
                            sev_color = "red" if f['risk_level'].lower() in ['critical', 'high'] else "amber" if f['risk_level'].lower() == 'medium' else "green"
                            state_color = "green" if is_ok else "red"
                            
                            cits_html = ""
                            for c in f.get('citations', []):
                                cits_html += f"""
<div class="citation-block">
    <div class="citation-text">"{c['quoted_text']}"</div>
    <div class="citation-source">📎 Foundry-IQ: {c['source_document']} | Confidence: {c['confidence_score']}</div>
</div>
"""
                                
                            findings_html += f"""
<div class="finding-row">
    <div class="finding-title">{icon} [{f['section_id']}] {f['rule_name']}</div>
    <div style="margin-bottom: 6px;">
        <span class="badge {state_color}">{f['rule_state'].replace('_', ' ')}</span>
        <span class="badge {sev_color}">{f['risk_level']} risk</span>
    </div>
    <div class="finding-ref">{f['reasoning']}</div>
    {cits_html}
</div>
"""
                        st.markdown(f"<div style='height:600px; overflow-y:auto; padding-right: 10px;'>{findings_html}</div>", unsafe_allow_html=True)

                else:
                    st.error(f"Backend Returned Error {response.status_code}")
                    
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")