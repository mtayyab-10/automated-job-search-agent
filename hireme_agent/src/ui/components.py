import streamlit as st


def show_header():
    """Displays the app branding with title, tagline, and a divider."""
    st.markdown(
        """
        <div style="text-align:center; padding: 8px 0 4px 0;">
          <h1 style="font-size:2.4rem; font-weight:800; margin:0;
                     background:linear-gradient(135deg,#6366f1,#8b5cf6,#ec4899);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                     background-clip:text;">
            🚀 HireMe
          </h1>
          <p style="color:#94a3b8; font-size:1rem; margin:4px 0 0 0; font-weight:500;">
            Your AI Career Co-Pilot — Find Jobs · Close Skill Gaps · Ace Interviews
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def show_error():
    """
    Checks if there is an error in session state.
    Displays it as a Streamlit error message and shows a dismiss button
    that clears the error and reruns the app.
    """
    if st.session_state.get("error") is not None:
        st.error(st.session_state.error)
        if st.button("Dismiss Error", key="dismiss_error_btn"):
            st.session_state.error = None
            st.rerun()


def show_cv_summary(cv_data: dict):
    """
    Takes the parsed CV dict and shows it inside a collapsed expander.
    Displays name, email, location, top skills, and preferred roles.
    """
    with st.expander("📄 Parsed CV Summary (click to review)", expanded=False):
        if not cv_data:
            st.write("No CV data available.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**👤 Name:** {cv_data.get('name', 'Not specified')}")
            st.markdown(f"**📧 Email:** {cv_data.get('email', 'Not specified')}")
            st.markdown(f"**📍 Location:** {cv_data.get('location', 'Not specified')}")
        with col2:
            skills = cv_data.get("skills", [])
            roles  = cv_data.get("preferred_roles", [])
            st.markdown(f"**🔧 Top Skills:** {', '.join(skills[:6]) if skills else 'None'}")
            st.markdown(f"**🎯 Preferred Roles:** {', '.join(roles) if roles else 'Auto-detected'}")

        experience = cv_data.get("experience", [])
        if experience:
            st.markdown("**💼 Experience:**")
            for exp in experience[:2]:
                title   = exp.get("title", "")
                company = exp.get("company", "")
                duration = exp.get("duration", "")
                st.markdown(f"  - {title} @ {company} ({duration})")
