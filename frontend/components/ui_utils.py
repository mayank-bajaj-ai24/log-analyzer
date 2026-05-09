import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    :root {
        --primary: #059669;
        --primary-dark: #064E3B;
        --secondary: #4F46E5;
        --bg-main: #F8FAFC;
        --bg-card: #FFFFFF;
        --text-main: #1E293B;
        --text-muted: #64748B;
        --border: #E2E8F0;
        --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    }

    .stApp {
        background-color: var(--bg-main);
        font-family: 'Inter', sans-serif;
    }

    /* Reduce Top Spacing but leave room for warnings */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 1rem !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }
    
    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }

    .sidebar-header {
        padding: 2rem 1rem 1rem 1rem;
        text-align: center;
    }

    .sidebar-logo {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #10B981 !important;
        letter-spacing: -0.025em;
    }

    /* Custom Page Link */
    .nav-link {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0.5rem;
        border-radius: 0.5rem;
        text-decoration: none;
        color: #94A3B8 !important;
        transition: all 0.2s ease;
    }

    .nav-link:hover {
        background-color: #1E293B;
        color: #F8FAFC !important;
    }

    .nav-link.active {
        background-color: #1E293B;
        color: #10B981 !important;
        font-weight: 600;
    }

    /* Hide Streamlit Branding but keep header for sidebar toggle */
    #MainMenu, footer {
        visibility: hidden;
    }

    /* Card Styling */
    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text-main);
        font-weight: 700 !important;
    }

    p, span, div {
        font-family: 'Inter', sans-serif;
    }

    /* Button Styling */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    </style>
    """, unsafe_allow_html=True)

def render_sidebar(active_page="overview"):
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            <div class="sidebar-logo">LOG ANALYZER</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.1em;">Enterprise Intelligence</div>
        </div>
        <div style="margin-top: 2rem;"></div>
        """, unsafe_allow_html=True)
        
        st.page_link("app.py", label="Dashboard Overview", icon=":material/dashboard:")
        st.page_link("pages/1_anomalies.py", label="Anomaly Engine", icon=":material/security:")
        st.page_link("pages/2_performance.py", label="System Metrics", icon=":material/speed:")
        st.page_link("pages/3_explore.py", label="Raw Log Explorer", icon=":material/search:")
        
        st.markdown("""
        <div style="position: fixed; bottom: 2rem; width: 15rem; padding: 1rem;">
            <div style="background: #1E293B; border-radius: 0.75rem; padding: 1rem; border: 1px solid #334155;">
                <div style="font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">System Status</div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                    <div style="width: 8px; height: 8px; background: #10B981; border-radius: 50%; box-shadow: 0 0 8px #10B981;"></div>
                    <div style="font-size: 0.85rem; color: #F8FAFC; font-weight: 500;">All Systems Nominal</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
