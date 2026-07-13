import streamlit as st
import streamlit.components.v1 as components
import json
from src.ui.components import show_header, show_error
from src.memory import cv_store


# ═══════════════════════════════════════════════════════════════════════════════
# Shared UI helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _score_bar(score: int, label: str = "Score") -> str:
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
    grade = "Strong" if score >= 70 else "Moderate" if score >= 45 else "Weak"
    return f"""
    <div style="margin:8px 0 18px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
        <span style="font-size:11px;color:#64748b;font-weight:700;letter-spacing:.6px;text-transform:uppercase;">{label}</span>
        <span style="font-size:20px;font-weight:800;color:{color};">{score}%
          <span style="font-size:11px;font-weight:600;color:{color}99;"> {grade}</span>
        </span>
      </div>
      <div style="background:#1e293b;border-radius:99px;height:8px;overflow:hidden;">
        <div style="background:linear-gradient(90deg,{color}55,{color});width:{score}%;height:100%;
                    border-radius:99px;"></div>
      </div>
    </div>"""


def _chip(text: str, color: str, bg: str) -> str:
    return (f'<span style="display:inline-block;background:{bg};color:{color};'
            f'border:1px solid {color}44;border-radius:999px;'
            f'padding:4px 14px;margin:3px 4px 3px 0;font-size:12px;font-weight:600;">{text}</span>')


def _copy_btn(text: str, uid: str, label: str = "📋 Copy") -> str:
    esc = json.dumps(text)
    return f"""
    <button id="cb-{uid}" style="background:#0f172a;color:#cbd5e1;border:1px solid #334155;
        padding:9px 18px;font-size:13px;border-radius:8px;cursor:pointer;
        font-family:Inter,sans-serif;font-weight:600;width:100%;transition:all .2s;">
      {label}
    </button>
    <script>
      document.getElementById('cb-{uid}').onclick = function() {{
        navigator.clipboard.writeText({esc}).then(()=>{{
          const b=document.getElementById('cb-{uid}');
          b.innerText='✅ Copied!';b.style.background='#166534';b.style.borderColor='#22c55e';b.style.color='#dcfce7';
          setTimeout(()=>{{b.innerText='{label}';b.style.background='#0f172a';b.style.borderColor='#334155';b.style.color='#cbd5e1';}},2000);
        }});
      }};
    </script>"""


def _reset():
    cv_store.clear_cv()
    for k, v in {"stage": "upload", "cv_data": None, "results": [], "roadmap": {},
                  "location": "", "count": 3, "error": None, "last_file": None}.items():
        st.session_state[k] = v
    for k in [k for k in st.session_state if k.startswith(("cover_letter_text_", "cold_body_", "fu_body_"))]:
        del st.session_state[k]


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Jobs & Cover Letters
# ═══════════════════════════════════════════════════════════════════════════════

def _tab_jobs(results):
    for i, r in enumerate(results):
        score = r.get("match_score", 0)
        ats   = r.get("ats_score", 0)
        sc    = "#22c55e" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
        ac    = "#22c55e" if ats   >= 70 else "#f59e0b" if ats   >= 45 else "#ef4444"
        sal_intel = r.get("salary_intel", {})
        verdict   = sal_intel.get("fairness_verdict", "")
        vc        = "#22c55e" if verdict == "Above Market" else "#f59e0b" if verdict == "Fair" else "#ef4444"

        # Build info line (company, location, salary, contract time)
        info_parts = []
        company = r.get("company", "").strip()
        if company:
            info_parts.append(f"🏢 <b>{company}</b>")
        
        location = r.get("location", "").strip()
        if location:
            info_parts.append(f"📍 {location}")
            
        salary = r.get("salary", "").strip()
        if salary and salary != "Not specified":
            info_parts.append(f"💰 {salary}")
            
        contract_time = r.get("contract_time", "").strip()
        if contract_time:
            time_str = contract_time.replace("_", " ").title()
            info_parts.append(f"⏱️ {time_str}")
            
        info_html = " &nbsp;·&nbsp; ".join(info_parts) if info_parts else "Not specified"

        # Build stats/scores line
        salary_box = ""
        if verdict:
            salary_box = (
                f'<div style="text-align:center;background:#020817;border:1px solid #1e293b;border-radius:10px;padding:8px 14px;">'
                f'<div style="font-size:9px;color:#64748b;font-weight:700;letter-spacing:.5px;">SALARY</div>'
                f'<div style="font-size:11px;font-weight:700;color:{vc};">{verdict}</div>'
                f'</div>'
            )

        html_content = (
            f'<div style="background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid #334155;border-radius:16px;padding:20px 24px;margin-bottom:12px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">'
            f'<div>'
            f'<h3 style="margin:0;color:#f1f5f9;font-size:1.15rem;font-weight:700;">{r.get("job_title","")}</h3>'
            f'<p style="margin:6px 0 0;color:#94a3b8;font-size:13px;">{info_html}</p>'
            f'</div>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
            f'<div style="text-align:center;background:#020817;border:1px solid #1e293b;border-radius:10px;padding:8px 14px;min-width:60px;">'
            f'<div style="font-size:9px;color:#64748b;font-weight:700;letter-spacing:.5px;">MATCH</div>'
            f'<div style="font-size:1.3rem;font-weight:800;color:{sc};">{score}%</div>'
            f'</div>'
            f'<div style="text-align:center;background:#020817;border:1px solid #1e293b;border-radius:10px;padding:8px 14px;min-width:60px;">'
            f'<div style="font-size:9px;color:#64748b;font-weight:700;letter-spacing:.5px;">ATS</div>'
            f'<div style="font-size:1.3rem;font-weight:800;color:{ac};">{ats}%</div>'
            f'</div>'
            f'{salary_box}'
            f'</div>'
            f'</div>'
            f'</div>'
        )

        st.markdown(html_content, unsafe_allow_html=True)

        if r.get("job_url"):
            st.link_button("🔗 Open Job Posting", url=r["job_url"])

        tk = f"cover_letter_text_{i}"
        if tk not in st.session_state:
            st.session_state[tk] = r.get("cover_letter", "")
        with st.expander("📝 Cover Letter — View & Edit", expanded=(i == 0)):
            edited = st.text_area("cl", value=st.session_state[tk], key=tk, height=300, label_visibility="collapsed")
            components.html(_copy_btn(edited, f"cl{i}", "📋 Copy Cover Letter"), height=52)

        st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Skill Gap Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def _tab_gaps(results):
    for r in results:
        st.markdown(f"<h4 style='color:#f1f5f9;margin-bottom:4px;'>{r.get('job_title','')} — {r.get('company','')}</h4>", unsafe_allow_html=True)
        st.markdown(_score_bar(r.get("match_score", 0), "Skill Match"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Your Strengths**")
            chips = "".join(_chip(s, "#22c55e", "#052e16") for s in r.get("candidate_strengths", []))
            st.markdown(chips or "*None extracted*", unsafe_allow_html=True)
        with c2:
            st.markdown("**⚠️ Skill Gaps**")
            chips = "".join(_chip(s, "#f87171", "#450a0a") for s in r.get("missing_skills", []))
            st.markdown(chips if chips else "<span style='color:#22c55e'>No significant gaps!</span>", unsafe_allow_html=True)
        resources = r.get("learning_resources", [])
        if resources:
            st.markdown("**📚 Free Learning Resources**")
            for res in resources:
                if res.get("skill") and res.get("resource"):
                    st.markdown(f"  🎯 **{res['skill']}** → [{res['resource']}]({res.get('url','#')})")
        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 3 — ATS Analyser
# ═══════════════════════════════════════════════════════════════════════════════

def _tab_ats(results):
    for i, r in enumerate(results):
        st.markdown(f"<h4 style='color:#f1f5f9;margin-bottom:4px;'>{r.get('job_title','')} — {r.get('company','')}</h4>", unsafe_allow_html=True)
        st.markdown(_score_bar(r.get("ats_score", 0), "ATS Keyword Match"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🟢 Keywords Found**")
            chips = "".join(_chip(k, "#34d399", "#022c22") for k in r.get("matched_keywords", []))
            st.markdown(chips or "*None detected*", unsafe_allow_html=True)
        with c2:
            st.markdown("**🔴 Missing Keywords**")
            chips = "".join(_chip(k, "#f87171", "#450a0a") for k in r.get("missing_keywords", []))
            st.markdown(chips if chips else "<span style='color:#22c55e'>All key terms present!</span>", unsafe_allow_html=True)
        tips = r.get("format_tips", [])
        if tips:
            st.markdown("**🛠️ Format Improvements**")
            for t in tips:
                st.markdown(f"  - {t}")
        opt = r.get("optimised_summary", "")
        if opt:
            st.markdown("**✨ ATS-Optimised Summary (add this to your CV)**")
            st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px 18px;color:#cbd5e1;font-size:14px;line-height:1.7;margin-bottom:8px;">{opt}</div>', unsafe_allow_html=True)
            components.html(_copy_btn(opt, f"ats{i}", "📋 Copy Optimised Summary"), height=52)
        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Salary Intelligence
# ═══════════════════════════════════════════════════════════════════════════════

_VERDICT_STYLE = {
    "Above Market": ("#22c55e", "#052e16", "🚀"),
    "Fair":         ("#f59e0b", "#451a03", "✅"),
    "Below Market": ("#ef4444", "#450a0a", "⚠️"),
}

def _tab_salary(results):
    for i, r in enumerate(results):
        si = r.get("salary_intel", {})
        verdict = si.get("fairness_verdict", "Unknown")
        vc, vbg, vicon = _VERDICT_STYLE.get(verdict, ("#94a3b8", "#0f172a", "❓"))
        pct = si.get("fairness_pct", 0)
        pct_str = f"+{pct}%" if pct > 0 else f"{pct}%"

        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
          <h4 style="color:#f1f5f9;margin:0 0 14px;">{r.get("job_title","")} @ {r.get("company","")}</h4>
          <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
            <div style="background:{vbg};border:1px solid {vc}33;border-radius:10px;padding:12px 18px;text-align:center;min-width:110px;">
              <div style="font-size:10px;color:{vc}99;font-weight:700;letter-spacing:.5px;">VERDICT</div>
              <div style="font-size:15px;font-weight:800;color:{vc};">{vicon} {verdict}</div>
              <div style="font-size:12px;color:{vc}88;font-weight:600;">{pct_str} vs market</div>
            </div>
            <div style="background:#020817;border:1px solid #1e293b;border-radius:10px;padding:12px 18px;text-align:center;min-width:110px;">
              <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:.5px;">POSTED</div>
              <div style="font-size:14px;font-weight:700;color:#e2e8f0;">{si.get("posted_salary","—")}</div>
            </div>
            <div style="background:#020817;border:1px solid #1e293b;border-radius:10px;padding:12px 18px;text-align:center;min-width:130px;">
              <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:.5px;">MARKET RANGE</div>
              <div style="font-size:13px;font-weight:700;color:#e2e8f0;">{si.get("market_low","—")} – {si.get("market_high","—")}</div>
            </div>
            <div style="background:#020817;border:1px solid #1e293b;border-radius:10px;padding:12px 18px;text-align:center;min-width:130px;">
              <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:.5px;">COUNTER OFFER</div>
              <div style="font-size:13px;font-weight:700;color:#818cf8;">{si.get("counter_offer_range","—")}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        pts = si.get("key_talking_points", [])
        if pts:
            st.markdown("**🗣️ Negotiation Talking Points**")
            for p in pts:
                st.markdown(f"  - {p}")

        script = si.get("negotiation_script", "")
        if script:
            st.markdown("**💬 What to Say in the Negotiation Meeting**")
            st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;border-left:3px solid #6366f1;border-radius:10px;padding:14px 18px;color:#cbd5e1;font-size:14px;line-height:1.8;margin-bottom:8px;font-style:italic;">"{script}"</div>', unsafe_allow_html=True)
            components.html(_copy_btn(script, f"sal{i}", "📋 Copy Negotiation Script"), height=52)

        seniority = si.get("seniority_level", "")
        if seniority:
            st.caption(f"Level assessment: **{seniority}** · ~{si.get('experience_years', 0)} years experience")
        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 5 — Interview Prep
# ═══════════════════════════════════════════════════════════════════════════════

_CAT_ICONS = {"Technical": "💻", "Behavioural": "⭐", "Motivation": "🎯", "Strengths": "💪", "Culture Fit": "🤝"}

def _tab_interview(results):
    labels = [f"{r.get('job_title','?')} — {r.get('company','')}" for r in results]
    sel = st.selectbox("Select role:", range(len(labels)), format_func=lambda x: labels[x], key="int_sel")
    r   = results[sel]
    prep = r.get("interview_prep", [])
    st.markdown(f"<h4 style='color:#f1f5f9;'>🎤 {r.get('job_title','')} at {r.get('company','')}</h4>", unsafe_allow_html=True)
    st.caption("5 questions tailored to this role + your CV. Click to reveal model answers.")
    st.divider()
    for idx, item in enumerate(prep, 1):
        cat  = item.get("category", "General")
        icon = _CAT_ICONS.get(cat, "❓")
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:16px 20px;margin-bottom:12px;">
          <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
            <span style="background:#1e293b;border-radius:999px;padding:3px 12px;font-size:11px;color:#94a3b8;font-weight:700;">{icon} {cat.upper()}</span>
            <span style="color:#475569;font-size:12px;">Q{idx}</span>
          </div>
          <p style="color:#f1f5f9;font-weight:700;font-size:15px;margin:0;">{item.get("question","")}</p>
        </div>""", unsafe_allow_html=True)
        with st.expander("💡 Show Model Answer", expanded=False):
            st.markdown(f'<p style="color:#cbd5e1;font-size:14px;line-height:1.8;margin:0;">{item.get("model_answer","")}</p>', unsafe_allow_html=True)
    st.divider()
    st.caption("💡 Practise saying each answer aloud — aim for under 2 minutes per question.")


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 6 — Email Drafter
# ═══════════════════════════════════════════════════════════════════════════════

def _tab_emails(results):
    labels = [f"{r.get('job_title','?')} — {r.get('company','')}" for r in results]
    sel = st.selectbox("Select role:", range(len(labels)), format_func=lambda x: labels[x], key="email_sel")
    r   = results[sel]
    cold = r.get("cold_email", {})
    fu   = r.get("followup_email", {})

    st.markdown("### 📨 Cold Application Email")
    st.markdown(f"**Subject:** `{cold.get('subject','')}`")
    ck = f"cold_body_{sel}"
    if ck not in st.session_state:
        st.session_state[ck] = cold.get("body", "")
    ce = st.text_area("cold", value=st.session_state[ck], key=ck, height=220, label_visibility="collapsed")
    components.html(_copy_btn(f"Subject: {cold.get('subject','')}\n\n{ce}", f"cold{sel}", "📋 Copy Cold Email"), height=52)

    st.markdown("---")
    st.markdown("### 🔁 Follow-Up Email *(send 5–7 days after applying)*")
    st.markdown(f"**Subject:** `{fu.get('subject','')}`")
    fk = f"fu_body_{sel}"
    if fk not in st.session_state:
        st.session_state[fk] = fu.get("body", "")
    fe = st.text_area("fu", value=st.session_state[fk], key=fk, height=160, label_visibility="collapsed")
    components.html(_copy_btn(f"Subject: {fu.get('subject','')}\n\n{fe}", f"fu{sel}", "📋 Copy Follow-Up Email"), height=52)


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 7 — 90-Day Career Roadmap
# ═══════════════════════════════════════════════════════════════════════════════

def _tab_roadmap(roadmap: dict):
    if not roadmap:
        st.info("No roadmap generated. Run a job search first.")
        return

    dream   = roadmap.get("dream_role", "")
    ready   = roadmap.get("readiness_score", 0)
    rc      = "#22c55e" if ready >= 70 else "#f59e0b" if ready >= 45 else "#ef4444"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border:1px solid #4338ca;
                border-radius:16px;padding:24px;margin-bottom:20px;text-align:center;">
      <div style="font-size:11px;color:#a5b4fc;font-weight:700;letter-spacing:1px;margin-bottom:8px;">YOUR DREAM ROLE</div>
      <div style="font-size:1.8rem;font-weight:900;color:#e0e7ff;margin-bottom:12px;">{dream}</div>
      <div style="font-size:11px;color:#a5b4fc;font-weight:700;letter-spacing:1px;margin-bottom:4px;">CURRENT READINESS</div>
      <div style="font-size:2.5rem;font-weight:900;color:{rc};">{ready}%</div>
    </div>""", unsafe_allow_html=True)

    # Weekly plan
    st.markdown("### 📅 90-Day Action Plan")
    weeks = [
        ("Week 1–4", "🚀 Quick Wins", roadmap.get("week_1_4", [])),
        ("Week 5–8", "🔨 Skill Building", roadmap.get("week_5_8", [])),
        ("Week 9–12", "🎯 Apply & Close", roadmap.get("week_9_12", [])),
    ]
    cols = st.columns(3)
    for col, (period, phase, actions) in zip(cols, weeks):
        with col:
            st.markdown(f"**{phase}**")
            st.caption(period)
            for a in actions:
                st.markdown(f"- {a}")

    st.divider()

    # Certifications
    certs = roadmap.get("top_certifications", [])
    if certs:
        st.markdown("### 🏆 Top Certifications by Salary ROI")
        for c in certs:
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
              <div>
                <b style="color:#f1f5f9;">{c.get("name","")}</b>
                <span style="color:#64748b;font-size:12px;"> · {c.get("provider","")}</span><br>
                <span style="color:#94a3b8;font-size:13px;">{c.get("roi_reason","")}</span>
              </div>
              <div style="text-align:right;">
                <span style="background:#1e293b;color:#818cf8;border-radius:999px;padding:3px 12px;font-size:12px;font-weight:700;">⏱️ {c.get("time_weeks",0)} weeks</span>
                &nbsp;<a href="{c.get("url","#")}" target="_blank" style="background:#312e81;color:#a5b4fc;border-radius:999px;padding:3px 12px;font-size:12px;font-weight:700;text-decoration:none;">Enrol →</a>
              </div>
            </div>""", unsafe_allow_html=True)

    # Portfolio projects
    projects = roadmap.get("portfolio_projects", [])
    if projects:
        st.divider()
        st.markdown("### 💻 Portfolio Projects to Build")
        for p in projects:
            with st.expander(f"📁 {p.get('title', 'Project')}", expanded=True):
                st.markdown(p.get("description", ""))
                st.code(p.get("tech_stack", ""), language="")
                st.info(f"💡 **Impact:** {p.get('impact', '')}")

    # LinkedIn targets
    targets = roadmap.get("linkedin_targets", [])
    if targets:
        st.divider()
        st.markdown("### 🔗 LinkedIn — Who to Connect With")
        chips = "".join(_chip(t, "#818cf8", "#1e1b4b") for t in targets)
        st.markdown(chips, unsafe_allow_html=True)

    # Power move
    power = roadmap.get("power_move", "")
    if power:
        st.divider()
        st.markdown("### ⚡ Your Power Move")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1e1b4b,#450a0a);border:1px solid #7c3aed44;
                    border-radius:14px;padding:20px 24px;">
          <div style="font-size:11px;color:#a78bfa;font-weight:700;letter-spacing:1px;margin-bottom:8px;">
            THE BOLD MOVE 95% OF CANDIDATES WON'T MAKE
          </div>
          <p style="color:#e0e7ff;font-size:14px;line-height:1.8;margin:0;">{power}</p>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Main page
# ═══════════════════════════════════════════════════════════════════════════════

def show_results_page():
    """Full results page with 7 tabs."""
    show_header()
    show_error()

    results = st.session_state.get("results", [])
    roadmap = st.session_state.get("roadmap", {})

    # Top bar
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h3 style='color:#f1f5f9;margin:0;'>🎯 {len(results)} Career Packages Ready</h3>", unsafe_allow_html=True)
    with col2:
        if st.button("↩ Start Over", use_container_width=True, key="start_over_btn"):
            _reset()
            st.rerun()

    if not results:
        st.warning("No jobs found. Try a different location or parameters.")
        return

    # Summary metrics
    avg_match = int(sum(r.get("match_score", 0) for r in results) / len(results))
    avg_ats   = int(sum(r.get("ats_score", 0)   for r in results) / len(results))
    best      = max(results, key=lambda r: r.get("match_score", 0))
    dream     = roadmap.get("dream_role", "")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 Jobs Analysed", len(results))
    m2.metric("🎯 Avg Match", f"{avg_match}%")
    m3.metric("🤖 Avg ATS Score", f"{avg_ats}%")
    m4.metric("🏆 Best Match", f"{best.get('job_title','')[:15]}…")

    if dream:
        st.markdown(
            f'<div style="background:#1e1b4b;border:1px solid #4338ca33;border-radius:10px;'
            f'padding:10px 18px;text-align:center;color:#a5b4fc;font-size:13px;font-weight:600;margin:8px 0;">'
            f'🗺️ Your Dream Role: <b style="color:#e0e7ff;">{dream}</b> &nbsp;·&nbsp; '
            f'Readiness: <b style="color:#818cf8;">{roadmap.get("readiness_score",0)}%</b>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # 7 tabs
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📋 Jobs & Cover Letters",
        "📊 Skill Gaps",
        "🤖 ATS Analyser",
        "💰 Salary Intel",
        "🎤 Interview Prep",
        "📧 Emails",
        "🗺️ 90-Day Roadmap",
    ])
    with t1: _tab_jobs(results)
    with t2: _tab_gaps(results)
    with t3: _tab_ats(results)
    with t4: _tab_salary(results)
    with t5: _tab_interview(results)
    with t6: _tab_emails(results)
    with t7: _tab_roadmap(roadmap)

    st.caption("HireMe Career Co-Pilot v3.0 · 9 Specialist Agents · Powered by Gemini AI + Adzuna")
