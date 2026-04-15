"""
TERRA Shared UI Components
"""
import streamlit as st
import streamlit.components.v1 as components


class UI:

    @staticmethod
    def inject_security_meta():
        components.html("""
        <script>
          // Prevent clickjacking
          if (window.self !== window.top) {
            window.top.location = window.self.location;
          }
        </script>
        """, height=0)

    @staticmethod
    def inject_global_styles():
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
          --green-dark:  #27500A;
          --green-mid:   #3B6D11;
          --green-light: #EAF3DE;
          --text-muted:  #6B7280;
          --card-bg:     #FFFFFF;
          --border:      rgba(0,0,0,0.08);
          --bg:          #F9FAFB;
        }

        @media (prefers-color-scheme: dark) {
          :root {
            --green-dark:  #97C459;
            --green-mid:   #639922;
            --green-light: #1a2a0a;
            --text-muted:  #9CA3AF;
            --card-bg:     #1F2937;
            --border:      rgba(255,255,255,0.08);
            --bg:          #111827;
          }
        }

        .stApp {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--bg);
        }

        #MainMenu, footer, header, .stDeployButton { display:none!important; }
        .block-container { max-width: 1200px !important; padding: 1rem 1.5rem !important; }

        /* Buttons */
        .stButton > button {
          background: var(--green-mid) !important;
          color: white !important;
          border: none !important;
          border-radius: 8px !important;
          font-weight: 500 !important;
          font-size: .9rem !important;
          padding: .5rem 1.2rem !important;
          transition: background .2s ease !important;
        }
        .stButton > button:hover {
          background: var(--green-dark) !important;
        }
        .stButton > button[kind="secondary"] {
          background: transparent !important;
          color: var(--green-mid) !important;
          border: 1.5px solid var(--green-mid) !important;
        }

        /* Form inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox select,
        .stTextArea textarea {
          border-radius: 8px !important;
          border: 1.5px solid var(--border) !important;
          font-size: .9rem !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
          border-color: var(--green-mid) !important;
          box-shadow: 0 0 0 3px rgba(59,109,17,0.15) !important;
        }

        /* Metrics */
        [data-testid="metric-container"] {
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: .75rem 1rem;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
          gap: 4px;
          border-bottom: 2px solid var(--border);
        }
        .stTabs [data-baseweb="tab"] {
          font-size: .9rem;
          font-weight: 500;
          border-radius: 8px 8px 0 0;
        }
        .stTabs [aria-selected="true"] {
          color: var(--green-mid) !important;
          border-bottom: 2px solid var(--green-mid) !important;
        }

        /* Sidebar */
        .css-1d391kg { background: var(--card-bg) !important; }

        /* Alerts */
        .stAlert { border-radius: 10px !important; }

        /* Checkbox */
        .stCheckbox label { font-size: .88rem !important; line-height: 1.5 !important; }

        /* Download button */
        .stDownloadButton > button {
          background: var(--green-light) !important;
          color: var(--green-dark) !important;
          border: 1.5px solid var(--green-mid) !important;
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_topbar(user=None, on_logout=None):
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.markdown("""
            <div style='display:flex;align-items:center;gap:.5rem;padding:.5rem 0;'>
              <span style='font-size:1.5rem;'>🌍</span>
              <span style='font-weight:700;font-size:1.1rem;color:var(--green-mid);'>TERRA</span>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            if user and on_logout:
                if st.button("Sign out", key="topbar_logout"):
                    on_logout()

    @staticmethod
    def metric_card(col, label, value, unit, delta=None, good=True):
        delta_color = "var(--green-mid)" if good else "#D85A30"
        delta_html  = f"<div style='font-size:.75rem;color:{delta_color};margin-top:2px;'>{delta}</div>" if delta else ""
        with col:
            st.markdown(f"""
            <div style='background:var(--card-bg);border:1px solid var(--border);
                 border-radius:12px;padding:1rem 1.2rem;height:100px;'>
              <div style='font-size:.72rem;color:var(--text-muted);font-weight:500;
                   text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem;'>
                {label}
              </div>
              <div style='font-size:1.6rem;font-weight:700;line-height:1.1;'>
                {value}
                <span style='font-size:.85rem;font-weight:400;color:var(--text-muted);'>
                  {unit}
                </span>
              </div>
              {delta_html}
            </div>
            """, unsafe_allow_html=True)