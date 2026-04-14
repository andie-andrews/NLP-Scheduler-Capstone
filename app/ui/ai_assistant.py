import os
from datetime import datetime

import streamlit as st

from llm.memory import ConversationMemory
from llm.orchestrator import run_orchestrator
from ui.theme import render_page_header


def render_ai_assistant():
    _inject_assistant_sticky_css()

    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    with st.container(key="assistant_sticky_header"):
        render_page_header(
            "🤖 AI Scheduler Assistant",
            "Ask for schedule help, shift summaries, and staffing insights in plain language.",
        )

        use_orchestrator_v2 = os.getenv("USE_ORCHESTRATOR_V2", "true").lower() == "true"
        st.caption(
            f"Using Orchestrator: {'V2 (OpenAPI)' if use_orchestrator_v2 else 'V1 (Legacy)'}"
        )

    with st.container(key="assistant_chat_history"):
        _render_chat_history()

    footer_cols = st.columns([5, 1], gap="small")
    with footer_cols[1]:
        if st.button("🆕 New chat", use_container_width=True):
            _start_new_chat()
            st.rerun()

    user_input = st.chat_input("Ask something about schedules, shifts, or hours...")
    if not user_input:
        return

    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    response = run_orchestrator(
        message=user_input,
        token=st.session_state.get("token"),
        session={
            "role": st.session_state.get("role"),
            "employee_id": st.session_state.get("employee_id"),
            "memory": st.session_state.memory,
        },
    )

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()


def _render_chat_history():
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            render_response(message["content"])


def _inject_assistant_sticky_css():
    st.markdown(
        """
        <style>
            .st-key-assistant_chat_history {
                height: calc(100vh - 23rem);
                min-height: 16rem;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 0.3rem 0.2rem 0.75rem 0.2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _start_new_chat():
    st.session_state.chat_messages = []
    st.session_state.memory = ConversationMemory()

    for key in (
        "pending_shift",
        "pending_delete_shift",
        "pending_show_shifts",
        "pending_update_shift",
    ):
        st.session_state.pop(key, None)


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
    # ✅ Structured responses (no raw JSON by default)
    # -------------------------------
    if isinstance(response, dict) and "data" in response:
        data = response.get("data", {}) or {}
        if response.get("summary"):
            st.markdown(response["summary"])

        if isinstance(data, dict) and "failedShifts" in data and data.get("failedShifts"):
            st.warning("Some shifts could not be created:")
            for failed in data.get("failedShifts", []):
                shift = failed.get("shift", {})
                start_value = shift.get("start", "unknown start")
                error_value = failed.get("error", "Validation failed")
                st.markdown(
                    f"- `{start_value}` ({shift.get('durationHours', '?')}h): {error_value}"
                )

        # Show lightweight metrics/details only when useful.
        if isinstance(data, dict) and "totalHours" in data:
            st.metric("Total Hours", data.get("totalHours", 0))
        return

    # -------------------------------
    # 🧠 Fallbacks
    # -------------------------------
    if isinstance(response, dict):
        if response.get("summary"):
            st.markdown(response["summary"])
        else:
            st.success("Done.")

    elif isinstance(response, list):
        st.success(f"Returned {len(response)} item(s).")

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
