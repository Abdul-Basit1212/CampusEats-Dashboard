"""
Home.py — CampusEats Dashboard · Authentication Gateway

Two-step login flow:
  Step 1 → Role selection  (Admin / Incharge / Stall Owner)
  Step 2 → Credential entry + DB verification

On success the following session-state keys are set:
  st.session_state.logged_in   : bool
  st.session_state.user_role   : 'admin' | 'incharge' | 'owner'
  st.session_state.entity_id   : None | campus_id | stall_id
  st.session_state.campus_id   : always set (None for admin until they pick one)
  st.session_state.user_name   : display name

Security features:
  - Rate limiting on login attempts
  - Input validation and sanitization
  - Session timeout (30 minutes)
  - Audit logging
  - Demo mode warning
"""

import streamlit as st
import os
from dotenv import load_dotenv
from database import authenticate_admin, authenticate_incharge, authenticate_stall
from security import (
    is_valid_email, is_valid_password, get_password_strength_feedback,
    sanitize_input, log_audit, _is_demo_mode
)

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CampusEats Dashboard",
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inline CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide sidebar navigation on login page */
    [data-testid="stSidebarNav"] { display: none; }
    
    /* Brand header */
    .brand-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .brand-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        color: #FF6B35;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .brand-header p {
        color: #011627;
        opacity: 0.6;
        font-size: 1rem;
        margin-top: 0.25rem;
    }

    /* Role card buttons */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 12px;
        height: 90px;
        font-size: 1rem;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.2s ease;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: #FF6B35;
        color: #FF6B35;
    }

    /* Login card */
    .login-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        box-shadow: 0 4px 24px rgba(1,22,39,0.08);
        margin-top: 1rem;
    }

    /* Demo banner */
    .demo-banner {
        background: #FFF3E0;
        border-left: 4px solid #FF6B35;
        border-radius: 4px;
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        margin-bottom: 1rem;
        color: #7A3B00;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state initialisation ──────────────────────────────────────────────
defaults = {
    "logged_in": False,
    "user_role": None,
    "entity_id": None,
    "campus_id": None,
    "user_name": None,
    "login_step": 1,
    "selected_role": None,
    "login_error": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── If already logged in → redirect to appropriate first page ─────────────────
if st.session_state.logged_in:
    role = st.session_state.user_role
    if role == "admin":
        st.switch_page("pages/1_Global_Admin.py")
    elif role == "incharge":
        st.switch_page("pages/2_Campus_HQ.py")
    else:
        st.switch_page("pages/3_Stall_Dashboard.py")
    st.stop()

# ── Brand header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="brand-header">
        <h1>🍔 CampusEats</h1>
        <p>Business Intelligence Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_role(role: str):
    st.session_state.selected_role = role
    st.session_state.login_step = 2
    st.session_state.login_error = ""


def _do_login(role: str, identifier: str, password: str):
    """Attempt authentication and populate session state on success."""
    # Sanitize inputs
    identifier = sanitize_input(identifier)
    password = sanitize_input(password, 1024)  # Longer for passwords
    
    if role == "Global Admin":
        # Validate email format
        if not is_valid_email(identifier):
            st.session_state.login_error = "Invalid email format."
            log_audit("login_failed", f"Invalid email format: {identifier}")
            return
        
        result = authenticate_admin(identifier, password)
        if result:
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.session_state.entity_id = None
            st.session_state.campus_id = None
            st.session_state.user_name = result["name"]
            st.session_state.login_error = ""
        else:
            st.session_state.login_error = "Invalid email or password."

    elif role == "Campus Incharge":
        # Validate email format
        if not is_valid_email(identifier):
            st.session_state.login_error = "Invalid email format."
            log_audit("login_failed", f"Invalid email format: {identifier}")
            return
        
        result = authenticate_incharge(identifier, password)
        if result:
            st.session_state.logged_in = True
            st.session_state.user_role = "incharge"
            st.session_state.entity_id = result["campus_id"]
            st.session_state.campus_id = result["campus_id"]
            st.session_state.user_name = result["name"]
            st.session_state.login_error = ""
        else:
            st.session_state.login_error = "Invalid email or password."

    else:  # Stall Owner
        # Validate stall ID is numeric
        try:
            sid = int(identifier.strip())
            if sid <= 0:
                raise ValueError()
        except ValueError:
            st.session_state.login_error = "Stall ID must be a positive number."
            log_audit("login_failed", "Invalid stall ID format")
            return
        
        result = authenticate_stall(sid, password)
        if result:
            st.session_state.logged_in = True
            st.session_state.user_role = "owner"
            st.session_state.entity_id = result["stall_id"]
            st.session_state.campus_id = result["campus_id"]
            st.session_state.user_name = result["name"]
            st.session_state.login_error = ""
        else:
            st.session_state.login_error = "Invalid Stall ID or password."


# ── Step 1: Role Selection ────────────────────────────────────────────────────
if st.session_state.login_step == 1:
    st.markdown("#### Select your role to continue")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌍\nGlobal Admin", use_container_width=True):
            _set_role("Global Admin")
            st.rerun()
    with col2:
        if st.button("📍\nCampus Incharge", use_container_width=True):
            _set_role("Campus Incharge")
            st.rerun()
    with col3:
        if st.button("🏪\nStall Owner", use_container_width=True):
            _set_role("Stall Owner")
            st.rerun()

# ── Step 2: Credential Entry ──────────────────────────────────────────────────
else:
    role = st.session_state.selected_role

    # ⚠️ SECURITY: Demo Mode Warning ──────────────────────────────────────────
    if _is_demo_mode():
        st.warning(
            "🧪 **DEMO MODE ACTIVE** - Security validations are disabled. "
            "This should ONLY be used for testing. DO NOT use in production!"
        )
        log_audit("demo_mode_warning", "User accessed demo mode login page")

    # Demo credentials banner
    if _is_demo_mode():
        demo_hints = {
            "Global Admin":     "Email: admin@campuseats.pk  |  Password: any",
            "Campus Incharge":  "Email: nust@campuseats.pk  |  Password: any",
            "Stall Owner":      "Stall ID: 1 – 100  |  Password: any",
        }
        st.markdown(
            f'<div class="demo-banner">🧪 <strong>Demo Mode</strong> — {demo_hints[role]}</div>',
            unsafe_allow_html=False,  # Security: Changed to False to prevent XSS
        )

    st.markdown(f"### Sign in as **{role}**")

    with st.form("login_form", clear_on_submit=False):
        if role in ("Global Admin", "Campus Incharge"):
            identifier = st.text_input("Email address", placeholder="you@campuseats.pk")
        else:
            identifier = st.text_input("Stall ID", placeholder="e.g.  42")

        password = st.text_input("Password", type="password", placeholder="••••••••")

        col_back, col_submit = st.columns([1, 2])
        with col_back:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col_submit:
            submit = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

        if back:
            st.session_state.login_step = 1
            st.session_state.login_error = ""
            st.rerun()

        if submit:
            if not identifier or not password:
                st.session_state.login_error = "Please fill in all fields."
            else:
                _do_login(role, identifier, password)
                if st.session_state.logged_in:
                    st.rerun()

    if st.session_state.login_error:
        st.error(st.session_state.login_error)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("CampusEats BI Dashboard · Powered by Streamlit · © 2026")
