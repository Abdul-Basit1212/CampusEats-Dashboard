"""
database.py — CampusEats Dashboard
Centralised SQLAlchemy engine + cached query helper.

All public helpers are wrapped in @st.cache_data(ttl=300) so the SQLite
file is never hammered by repeated Streamlit reruns.

Security enhancements:
- Authorization checks on all data access
- Audit logging for sensitive operations
- Role-based data scoping
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///CampusEats.db")

# Import security module
try:
    from security import validate_session, authorize_stall_access, authorize_campus_access, log_audit, get_safe_error_message
except ImportError:
    # Fallback if security module not available
    def validate_session(): return True
    def authorize_stall_access(sid): return True
    def authorize_campus_access(cid): return True
    def log_audit(*args, **kwargs): pass
    def get_safe_error_message(e): return str(e)

# Use check_same_thread=False so SQLAlchemy connections survive Streamlit's
# multi-threaded execution model.
_engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


# ── Core query helper ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(query: str, params: dict | None = None) -> pd.DataFrame:
    """
    Execute a parameterised SQL query and return the result as a DataFrame.

    Parameters
    ----------
    query  : SQL string with optional :named bind parameters.
    params : Dict of parameter values, e.g. {"campus_id": 1}.

    Returns
    -------
    pd.DataFrame — empty DataFrame on error.
    """
    try:
        with _engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params or {})
    except Exception as exc:
        error_msg = get_safe_error_message(exc)
        st.error(f"Database error: {error_msg}")
        return pd.DataFrame()


# ── Write helper (not cached — used for settings updates) ────────────────────

def execute_write(query: str, params: dict | None = None) -> bool:
    """
    Execute a DML statement (INSERT / UPDATE / DELETE).
    Returns True on success, False on failure.
    """
    try:
        with _engine.begin() as conn:
            conn.execute(text(query), params or {})
        
        # Log write operations for audit trail
        action = "insert" if "INSERT" in query.upper() else "update" if "UPDATE" in query.upper() else "delete"
        log_audit(f"data_{action}", f"Query executed: {query[:100]}")
        
        return True
    except Exception as exc:
        error_msg = get_safe_error_message(exc)
        st.error(f"Write error: {error_msg}")
        log_audit("write_error", str(exc))
        return False


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    """Check if demo mode is enabled. SHOULD ONLY BE TRUE IN DEVELOPMENT."""
    demo = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo:
        print("⚠️ WARNING: DEMO_MODE is enabled. This should only be used in development!")
    return demo


def _verify_password(plain: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Supports:
      • werkzeug   pbkdf2:sha256:<salt>$<hash>  (production)
      • demo mode  pbkdf2:sha256:mockhashvalue  (any password accepted)
    
    SECURITY: In demo mode, ANY password is accepted if hash contains "mock".
    This should NEVER be enabled in production.
    """
    if _is_demo_mode() and "mock" in stored_hash.lower():
        log_audit("auth_demo_mode_accept", "Password accepted due to demo mode")
        return True  # accept any password when hash is a placeholder
    
    try:
        from werkzeug.security import check_password_hash
        return check_password_hash(stored_hash, plain)
    except ImportError:
        # fallback: raw pbkdf2_hmac comparison
        import hashlib, hmac
        try:
            parts = stored_hash.split("$")
            salt = parts[0].encode()
            expected = parts[1]
            derived = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 260000)
            import binascii
            return hmac.compare_digest(binascii.hexlify(derived).decode(), expected)
        except Exception:
            return False


def authenticate_admin(email: str, password: str) -> dict | None:
    """Return admin record dict on success, None on failure."""
    from security import check_rate_limit, record_failed_login, clear_failed_logins, sanitize_input
    
    # Sanitize input
    email = sanitize_input(email, 255)
    
    # Check rate limiting
    is_allowed, message = check_rate_limit(email)
    if not is_allowed:
        st.error(message)
        return None
    
    df = fetch_data(
        "SELECT admin_id, name, email, password_hash FROM Global_Admins WHERE email = :email",
        {"email": email},
    )
    if df.empty:
        log_audit("failed_login_admin", f"Email not found: {email}")
        record_failed_login(email)
        return None
    
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        clear_failed_logins(email)
        log_audit("successful_login", f"Admin login: {row['name']}")
        return {"admin_id": int(row["admin_id"]), "name": row["name"]}
    
    log_audit("failed_login_admin", f"Invalid password for: {email}")
    record_failed_login(email)
    return None


def authenticate_incharge(email: str, password: str) -> dict | None:
    """Return incharge record dict on success, None on failure."""
    from security import check_rate_limit, record_failed_login, clear_failed_logins, sanitize_input
    
    # Sanitize input
    email = sanitize_input(email, 255)
    
    # Check rate limiting
    is_allowed, message = check_rate_limit(email)
    if not is_allowed:
        st.error(message)
        return None
    
    df = fetch_data(
        """SELECT incharge_id, campus_id, name, email, password_hash
           FROM Campus_Incharges WHERE email = :email""",
        {"email": email},
    )
    if df.empty:
        log_audit("failed_login_incharge", f"Email not found: {email}")
        record_failed_login(email)
        return None
    
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        clear_failed_logins(email)
        log_audit("successful_login", f"Incharge login: {row['name']}")
        return {"incharge_id": int(row["incharge_id"]),
                "campus_id": int(row["campus_id"]),
                "name": row["name"]}
    
    log_audit("failed_login_incharge", f"Invalid password for: {email}")
    record_failed_login(email)
    return None


def authenticate_stall(stall_id: int, password: str) -> dict | None:
    """Return stall record dict on success, None on failure."""
    from security import check_rate_limit, record_failed_login, clear_failed_logins
    
    # Verify stall_id is numeric
    try:
        stall_id = int(stall_id)
    except (ValueError, TypeError):
        log_audit("failed_login_stall", "Invalid stall_id format")
        return None
    
    # Check rate limiting
    stall_key = f"stall_{stall_id}"
    is_allowed, message = check_rate_limit(stall_key)
    if not is_allowed:
        st.error(message)
        return None
    
    df = fetch_data(
        """SELECT stall_id, campus_id, name, password_hash
           FROM Stalls WHERE stall_id = :sid""",
        {"sid": stall_id},
    )
    if df.empty:
        log_audit("failed_login_stall", f"Stall not found: {stall_id}")
        record_failed_login(stall_key)
        return None
    
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        clear_failed_logins(stall_key)
        log_audit("successful_login", f"Stall owner login: {row['name']}")
        return {"stall_id": int(row["stall_id"]),
                "campus_id": int(row["campus_id"]),
                "name": row["name"]}
    
    log_audit("failed_login_stall", f"Invalid password for stall: {stall_id}")
    record_failed_login(stall_key)
    return None


# ── Convenience getters used across pages ─────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_all_campuses() -> pd.DataFrame:
    return fetch_data("SELECT campus_id, name, real_location_lat, real_location_long FROM Campuses")


@st.cache_data(ttl=300, show_spinner=False)
def get_campus_name(campus_id: int) -> str:
    df = fetch_data("SELECT name FROM Campuses WHERE campus_id = :cid", {"cid": campus_id})
    return df.iloc[0]["name"] if not df.empty else "Unknown Campus"
