import streamlit as st
from llm.orchestrator import run_orchestrator
from llm.memory import ConversationMemory
import config as config
from datetime import datetime


def render_ai_assistant():
    st.header("🤖 AI Scheduler Assistant")

    # -------------------------------
    # 🧠 Memory (session)
    # -------------------------------
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()

    # -------------------------------
    # 🧪 Debug: which orchestrator
    # -------------------------------
    st.caption(
        f"Using Orchestrator: {'V2 (OpenAPI)' if config.USE_ORCHESTRATOR_V2 else 'V1 (Legacy)'}"
    )

    # -------------------------------
    # 💬 User Input
    # -------------------------------
    user_input = st.text_input("Ask something...")

    if user_input:
        response = run_orchestrator(
            message=user_input,
            token=st.session_state.get("token"),
            session={
                "role": st.session_state.get("role"),
                "employee_id": st.session_state.get("employee_id"),
                "memory": st.session_state.memory,
            },
        )

        render_response(response)


def render_response(response):

    if not response:
        st.info("No response.")
        return

    # -------------------------------
    # 🎯 SHIFT SUMMARY UI
    # -------------------------------
    if isinstance(response, dict) and "data" in response:

        data = response["data"]
        

        # 📊 Metrics row
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Hours", data.get("totalHours", 0))

        with col2:
            st.metric("Total Shifts", len(data.get("shifts", [])))

        st.divider()

        # 📅 Shift Cards
        for shift in data.get("shifts", []):
            with st.container():
                cols = st.columns([2, 2, 1])

                with cols[0]:
                    st.markdown(f"**📅 {format_date(shift['start'])}**")

                with cols[1]:
                    st.markdown(f"🕒 {format_time(shift['start'])}")

                with cols[2]:
                    st.markdown(f"⏱️ **{shift['durationHours']} hrs**")

                st.divider()

        return

    # -------------------------------
    # 🧠 Fallbacks
    # -------------------------------
    if isinstance(response, dict):
        st.json(response)

    elif isinstance(response, list):
        st.json(response)

    else:
        st.success(response)


def format_date(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%A, %b %d")

def format_time(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%I:%M %p")