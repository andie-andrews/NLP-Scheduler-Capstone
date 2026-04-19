import streamlit as st


def inject_global_styles() -> None:
    """Apply a light, modern visual theme across the app."""
    st.markdown(
        """
        <style>
            html, body {
                font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif !important;
            }

            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] *,
            [data-testid="stSidebar"],
            [data-testid="stSidebar"] * {
                color: #1f2a44 !important;
            }

            :root,
            [data-theme="dark"] {
                --background-color: #f7fbff;
                --secondary-background-color: #ffffff;
                --text-color: #1f2a44;
            }

            .stApp {
                background: linear-gradient(180deg, #f7fbff 0%, #eef4ff 55%, #f5f7ff 100%);
            }

            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > .main,
            [data-testid="stAppViewContainer"] > .main > div {
                background: transparent !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #f8fbff 0%, #f1f5ff 100%);
                border-right: 1px solid #dbe7ff;
            }

            [data-testid="stHeader"] {
                background: linear-gradient(180deg, rgba(248, 251, 255, 0.95) 0%, rgba(239, 245, 255, 0.95) 100%) !important;
                border-bottom: 1px solid #dbe7ff !important;
            }

            [data-testid="stToolbar"],
            [data-testid="stToolbar"] *,
            [data-testid="stStatusWidget"],
            [data-testid="stStatusWidget"] *,
            [data-testid="stToolbarActions"],
            [data-testid="stMainMenu"],
            [data-testid="stMainMenu"] * {
                color: #1f2a44 !important;
            }

            [data-testid="stHeader"] [data-testid="stBaseButton-header"],
            [data-testid="stMainMenuButton"] {
                background: #ffffff !important;
                color: #1f2a44 !important;
                border: 1px solid #c9dafd !important;
                border-radius: 8px !important;
            }

            [data-testid="stHeader"] [data-testid="stBaseButton-header"]:hover,
            [data-testid="stMainMenuButton"]:hover {
                background: #edf4ff !important;
                border-color: #b7cdfa !important;
                color: #13213f !important;
            }

            [data-testid="stSidebar"] * {
                color: #1f2a44;
            }

            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] li,
            [data-testid="stMarkdownContainer"] span,
            [data-testid="stMetricValue"],
            [data-testid="stMetricLabel"],
            [data-testid="stChatMessage"] {
                color: #1f2a44 !important;
                opacity: 1 !important;
            }

            [data-testid="stChatMessage"] {
                background: #ffffff !important;
                border: 1px solid #dbe7ff !important;
                border-radius: 12px !important;
                padding: 0.4rem 0.75rem !important;
            }

            [data-testid="stSidebar"] [data-testid="stButton"] > button,
            [data-testid="stAppViewContainer"] [data-testid="stButton"] > button {
                min-height: 2rem;
                border-radius: 10px !important;
                font-weight: 600 !important;
                background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%) !important;
                color: #1f2a44 !important;
                border: 1px solid #c9dafd !important;
                box-shadow: 0 1px 2px rgba(31, 42, 68, 0.08) !important;
            }

            [data-testid="stSidebar"] [data-testid="stButton"] > button:hover,
            [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:hover {
                background: linear-gradient(180deg, #f8fbff 0%, #edf4ff 100%) !important;
                border-color: #b7cdfa !important;
                color: #13213f !important;
            }

            [data-testid="stSidebar"] [data-testid="stButton"] > button:disabled,
            [data-testid="stAppViewContainer"] [data-testid="stButton"] > button:disabled {
                background: #eef3fc !important;
                color: #7a8aa9 !important;
                border-color: #d7e2f7 !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stAppViewContainer"] [data-baseweb="select"] > div {
                background: #ffffff !important;
                color: #1f2a44 !important;
                border: 1px solid #c9dafd !important;
                border-radius: 10px !important;
            }

            [data-baseweb="popover"] [role="listbox"],
            [data-baseweb="popover"] [role="option"] {
                background: #ffffff !important;
                color: #1f2a44 !important;
            }

            [data-testid="stChatInput"] textarea {
                background: #ffffff !important;
                color: #1f2a44 !important;
                border: 1px solid #dbe7ff !important;
                border-radius: 10px !important;
            }

            .app-shell {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid #dbe7ff;
                border-radius: 16px;
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
                box-shadow: 0 10px 26px rgba(92, 118, 255, 0.08);
                backdrop-filter: blur(4px);
            }

            .page-title {
                font-size: 1.7rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 0.25rem;
                letter-spacing: 0.01em;
            }

            .page-subtitle {
                color: #4b5d7a;
                margin-bottom: 0.1rem;
                font-size: 0.95rem;
            }

            .metric-tile {
                border: 1px solid #dbe7ff;
                border-radius: 12px;
                padding: 0.85rem;
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .section-card {
                border: 1px solid #dbe7ff;
                border-radius: 12px;
                padding: 0.85rem 1rem;
                margin-bottom: 0.6rem;
                background: #ffffff;
            }

            .sidebar-brand {
                font-size: 1.08rem;
                font-weight: 700;
                color: #2b3a67;
                margin-bottom: 0.35rem;
            }

            .sidebar-muted {
                color: #60708f;
                font-size: 0.85rem;
            }

            .sidebar-user {
                background: #ffffff;
                border: 1px solid #dbe7ff;
                border-radius: 12px;
                padding: 0.7rem 0.8rem;
                margin-bottom: 0.8rem;
            }

            .sidebar-user--employee {
                background: #fff4e6;
                border-color: #ffd8a8;
            }

            .sidebar-user--supervisor {
                background: #e8f7ec;
                border-color: #b7e4c7;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="app-shell">
            <div class="page-title">{title}</div>
            <div class="page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
