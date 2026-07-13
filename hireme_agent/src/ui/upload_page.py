import streamlit as st
import streamlit.components.v1 as components
from src.ui.components import show_header, show_error, show_cv_summary
from src.parsers import ingest_cv
from src.agents import run_orchestrator
from src.memory import cv_store


# ── Animated agent pipeline diagram ───────────────────────────────────────────

PIPELINE_HTML = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  .pipeline-wrap {
    font-family: 'Inter', sans-serif;
    background: #020817;
    padding: 24px 8px 12px;
    border-radius: 16px;
  }
  .pipeline-title {
    text-align: center;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 20px;
  }
  .pipeline-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    flex-wrap: nowrap;
    overflow-x: auto;
  }
  .agent-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 90px;
  }
  .agent-icon {
    width: 52px; height: 52px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    background: #0f172a;
    border: 1px solid #1e293b;
    position: relative;
    transition: transform .3s ease, box-shadow .3s ease;
    animation: pulse-border 3s ease-in-out infinite;
  }
  .agent-icon:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px #6366f155;
  }
  .agent-label {
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
    text-align: center;
    line-height: 1.3;
  }
  .arrow {
    color: #334155;
    font-size: 20px;
    margin: 0 2px;
    flex-shrink: 0;
    margin-bottom: 24px;
  }
  /* Individual delays */
  .n1 { animation-delay: 0s; }
  .n2 { animation-delay: .4s; }
  .n3 { animation-delay: .8s; }
  .n4 { animation-delay: 1.2s; }
  .n5 { animation-delay: 1.6s; }
  .n6 { animation-delay: 2s; }
  .n7 { animation-delay: 2.4s; }
  .n8 { animation-delay: 2.8s; }
  .n9 { animation-delay: 3.2s; }

  @keyframes pulse-border {
    0%, 100% { border-color: #1e293b; box-shadow: none; }
    50%       { border-color: #6366f1; box-shadow: 0 0 16px #6366f133; }
  }
</style>
<div class="pipeline-wrap">
  <div class="pipeline-title">9-Agent Career Co-Pilot Pipeline</div>
  <div class="pipeline-row">
    <div class="agent-node">
      <div class="agent-icon n1">🔍</div>
      <div class="agent-label">Search<br>Agent</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n2">🌐</div>
      <div class="agent-label">Scraper<br>Agent</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n3">📊</div>
      <div class="agent-label">Gap<br>Analyst</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n4">🤖</div>
      <div class="agent-label">ATS<br>Analyser</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n5">✍️</div>
      <div class="agent-label">Writer<br>Agent</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n6">🎤</div>
      <div class="agent-label">Interview<br>Agent</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n7">📧</div>
      <div class="agent-label">Email<br>Drafter</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n8">💰</div>
      <div class="agent-label">Salary<br>Intel</div>
    </div>
    <div class="arrow">→</div>
    <div class="agent-node">
      <div class="agent-icon n9">🗺️</div>
      <div class="agent-label">Career<br>Roadmap</div>
    </div>
  </div>
</div>
"""



def show_upload_page():
    """
    Renders the upload page with:
    - Animated multi-agent pipeline diagram
    - CV upload & parsing
    - Location + count preferences
    - Launch button that drives the orchestrator with a live status feed
    """
    show_header()
    show_error()

    # ── Pipeline diagram ───────────────────────────────────────────────────────
    components.html(PIPELINE_HTML, height=140)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── File uploader ──────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "📄 Upload your CV (PDF or DOCX)",
        type=["pdf", "docx"],
        help="Your CV is parsed locally — we extract your skills, experience, and education.",
    )

    if uploaded_file is not None:
        if st.session_state.get("last_file") != uploaded_file.name:
            with st.spinner("🔍 Parsing CV with Gemini AI…"):
                try:
                    parsed_cv = ingest_cv(uploaded_file)
                    st.session_state.cv_data = parsed_cv
                    st.session_state.last_file = uploaded_file.name
                    st.session_state.error = None
                    st.rerun()
                except Exception as e:
                    st.session_state.error = f"Failed to parse CV: {e}"
                    st.session_state.cv_data = None
                    st.session_state.last_file = uploaded_file.name
                    st.rerun()
    else:
        if st.session_state.get("last_file") is not None:
            st.session_state.cv_data = None
            st.session_state.last_file = None
            cv_store.clear_cv()
            st.rerun()

    # Sync memory store across Streamlit re-runs
    if st.session_state.cv_data is not None and not cv_store.is_cv_loaded():
        cv_store.save_cv(st.session_state.cv_data)

    # Show parsed CV summary if loaded
    if st.session_state.cv_data is not None:
        show_cv_summary(st.session_state.cv_data)

    # ── Search preferences ─────────────────────────────────────────────────────
    st.markdown("### 🎯 Search Preferences")

    LOCATION_OPTIONS = [
        "Remote (Global)",
        "London, UK",
        "Manchester, UK",
        "Edinburgh, UK",
        "New York, US",
        "San Francisco, US",
        "Chicago, US",
        "Seattle, US",
        "Toronto, Canada",
        "Sydney, Australia",
        "Melbourne, Australia",
        "Bangalore, India",
        "Mumbai, India",
        "Delhi, India",
        "Berlin, Germany",
        "Amsterdam, Netherlands",
    ]
    LOC_MAP = {
        "Remote (Global)": "Remote",
        "London, UK": "London",
        "Manchester, UK": "Manchester",
        "Edinburgh, UK": "Edinburgh",
        "New York, US": "New York",
        "San Francisco, US": "San Francisco",
        "Chicago, US": "Chicago",
        "Seattle, US": "Seattle",
        "Toronto, Canada": "Toronto",
        "Sydney, Australia": "Sydney",
        "Melbourne, Australia": "Melbourne",
        "Bangalore, India": "Bangalore",
        "Mumbai, India": "Mumbai",
        "Delhi, India": "Delhi",
        "Berlin, Germany": "Berlin",
        "Amsterdam, Netherlands": "Amsterdam",
    }

    col1, col2 = st.columns(2)
    with col1:
        location_preset = st.selectbox(
            "Job Market",
            options=LOCATION_OPTIONS,
            index=0,
            key="location_preset",
            help="Select the job market you want to search. Adzuna covers UK, US, Canada, Australia, India & Europe.",
        )
        st.session_state.location = LOC_MAP.get(location_preset, location_preset)
        st.caption(f"🔍 Will search: **{st.session_state.location}**")
    with col2:
        st.selectbox("Number of Jobs to Analyse", options=[3, 5, 10], key="count")

    st.markdown(
        '<div style="background:#0f172a;border:1px solid #334155;border-left:3px solid #f59e0b;'
        'border-radius:8px;padding:10px 16px;margin:8px 0;font-size:12px;color:#94a3b8;">'
        '💡 <b>Pakistan / Gulf users:</b> Adzuna does not cover PK/AE directly. '
        'Select <b>Remote (Global)</b> or <b>London, UK</b> to find remote-friendly roles you can apply to from anywhere.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Launch button ──────────────────────────────────────────────────────────
    cv_loaded      = st.session_state.cv_data is not None
    location_value = st.session_state.get("location", "").strip()
    button_disabled = not cv_loaded

    st.divider()
    find_jobs_btn = st.button(
        "🚀 Launch Career Co-Pilot",
        use_container_width=True,
        disabled=button_disabled,
    )

    if button_disabled:
        st.caption("⚠️ Please upload your CV to get started.")

    # ── Multi-agent pipeline with live status feed ─────────────────────────────
    if find_jobs_btn:
        log_messages: list[str] = []

        with st.status("🤖 9-Agent Pipeline Initialising…", expanded=True) as status_box:
            log_area = st.empty()

            def status_callback(msg: str):
                log_messages.append(msg)
                log_area.markdown("\n\n".join(log_messages))

            try:
                output = run_orchestrator(
                    location=st.session_state.location,
                    count=st.session_state.count,
                    status_callback=status_callback,
                )
                job_results = output.get("jobs", [])
                roadmap     = output.get("roadmap", {})

                status_box.update(
                    label=f"✅ Done! {len(job_results)} career packages ready.",
                    state="complete",
                    expanded=False,
                )
                st.session_state.results = job_results
                st.session_state.roadmap = roadmap
                st.session_state.stage   = "results"
                st.session_state.error   = None
                st.rerun()

            except Exception as e:
                status_box.update(label="❌ Pipeline failed", state="error", expanded=True)
                st.session_state.error = f"Agent Error: {e}"
                st.rerun()
