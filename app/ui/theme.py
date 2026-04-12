import streamlit as st


def inject_global_styles() -> None:
    """Apply a consistent, professional visual theme across the app."""
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            }

            [data-testid="stSidebar"] {
                background: #0f172a;
            }

            [data-testid="stSidebar"] * {
                color: #e2e8f0;
            }

            .app-shell {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            }

            .page-title {
                font-size: 1.7rem;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 0.25rem;
            }

            .page-subtitle {
                color: #475569;
                margin-bottom: 0.1rem;
                font-size: 0.95rem;
            }

            .metric-tile {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 0.85rem;
                background: #f8fafc;
            }

            .section-card {
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 0.85rem 1rem;
                margin-bottom: 0.6rem;
                background: #ffffff;
            }

            .sidebar-brand {
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 0.8rem;
            }

            .sidebar-muted {
                color: #94a3b8;
                font-size: 0.9rem;
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
