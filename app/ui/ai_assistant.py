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
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # -------------------------------
    # 🧪 Debug: which orchestrator
    # -------------------------------
    st.caption(
        f"Using Orchestrator: {'V2 (OpenAPI)' if config.USE_ORCHESTRATOR_V2 else 'V1 (Legacy)'}"
    )

    _render_chat_history()

    # -------------------------------
    # 💬 Chat Input (interactive)
    # -------------------------------
    user_input = st.chat_input("Ask something about schedules, shifts, or hours...")
    if not user_input:
        return

    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
    })

    response = run_orchestrator(
        message=user_input,
        token=st.session_state.get("token"),
        session={
            "role": st.session_state.get("role"),
            "employee_id": st.session_state.get("employee_id"),
            "memory": st.session_state.memory,
        },
    )

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": response,
    })
    st.rerun()


def _render_chat_history():
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            render_response(message["content"])


def render_response(response):

    if not response:
        st.info("No response.")
        return

    # -------------------------------
    # 🎯 Rich Shift Summary UI
    # -------------------------------
    if (
        isinstance(response, dict)
        and "data" in response
        and isinstance(response.get("data"), dict)
        and "shifts" in response["data"]
    ):

        data = response["data"]
        if response.get("summary"):
            st.markdown(response["summary"])

        # 📊 Metrics row
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Hours", data.get("totalHours", 0))

        with col2:
            st.metric("Total Shifts", len(data.get("shifts", [])))

        st.divider()

        # 📅 Shift Cards (for list results)
        for shift in data.get("shifts", []):
            _render_shift_card(shift)

        return

    # -------------------------------
    # ✅ Created shift payload
    # -------------------------------
    if isinstance(response, dict) and "data" in response:
        if response.get("summary"):
            st.markdown(response["summary"])
        st.json(response["data"])
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


def _render_shift_card(shift: dict):
    with st.container():
        cols = st.columns([2, 2, 1])

        with cols[0]:
            st.markdown(f"**📅 {format_date(shift['start'])}**")

        with cols[1]:
            st.markdown(f"🕒 {format_time(shift['start'])}")

        with cols[2]:
            st.markdown(f"⏱️ **{shift['durationHours']} hrs**")

        st.divider()
