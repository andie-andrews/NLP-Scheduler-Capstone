import streamlit as st


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
            }

            .app-page-title {
                font-size: 1.65rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
                letter-spacing: 0.2px;
            }

            .app-page-subtitle {
                color: #6b7280;
                font-size: 0.95rem;
                margin-bottom: 1rem;
            }

            .app-card {
                border: 1px solid rgba(100, 116, 139, 0.25);
                background: rgba(248, 250, 252, 0.5);
                border-radius: 0.75rem;
                padding: 0.9rem 1rem;
                margin-bottom: 0.75rem;
            }

            .app-pill {
                display: inline-block;
                font-size: 0.75rem;
                border: 1px solid rgba(148, 163, 184, 0.4);
                border-radius: 999px;
                padding: 0.2rem 0.6rem;
                margin-right: 0.4rem;
                color: #334155;
                background: #f8fafc;
            }

            [data-testid="stSidebar"] .profile-card {
                border: 1px solid rgba(100, 116, 139, 0.35);
                border-radius: 0.75rem;
                padding: 0.7rem 0.8rem;
                margin-bottom: 1rem;
                background: rgba(248, 250, 252, 0.5);
            }

            [data-testid="stSidebar"] .profile-name {
                font-weight: 600;
                margin-bottom: 0.2rem;
            }

            [data-testid="stSidebar"] .profile-role {
                color: #64748b;
                font-size: 0.86rem;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.5rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"<div class='app-page-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='app-page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
