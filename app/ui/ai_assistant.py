import streamlit as st
from llm.orchestrator import handle_request
from llm.memory import ConversationMemory


def render_ai_assistant():
    st.header("🤖 AI Scheduler Assistant")

    # -------------------------------
    # 🧠 Memory (session)
    # -------------------------------
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()

    user_input = st.text_input("Ask something...")

    if user_input:
        response = handle_request(
            user_input,
            role=st.session_state.get("role"),
            token=st.session_state.get("token"),
            memory=st.session_state.memory,
            employee_id=st.session_state.get("employee_id")
        )

        # -------------------------------
        # 🎯 Response Handling
        # -------------------------------
        if not response:
            st.info("No response.")

        elif isinstance(response, dict):
            if response.get("type") == "disambiguation":
                st.warning("Multiple matches found. Please clarify:")
                for i, option in enumerate(response["options"]):
                    st.write(f"{i+1}. {option}")
            else:
                st.json(response)

        elif isinstance(response, list):
            if len(response) == 0:
                st.info("No data found.")
            else:
                st.json(response)

        else:
            st.success(response)