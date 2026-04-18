"""
database.py — CampusEats Dashboard
Centralised SQLAlchemy engine + cached query helper.

All public helpers are wrapped in @st.cache_data(ttl=300) so the SQLite
file is never hammered by repeated Streamlit reruns.
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///CampusEats.db")

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
        st.error(f"Database error: {exc}")
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
        return True
    except Exception as exc:
        st.error(f"Write error: {exc}")
        return False


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def _verify_password(plain: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Supports:
      • werkzeug   pbkdf2:sha256:<salt>$<hash>  (production)
      • demo mode  pbkdf2:sha256:mockhashvalue  (any password accepted)
    """
    if _is_demo_mode() and "mock" in stored_hash.lower():
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
    df = fetch_data(
        "SELECT admin_id, name, email, password_hash FROM Global_Admins WHERE email = :email",
        {"email": email},
    )
    if df.empty:
        return None
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        return {"admin_id": int(row["admin_id"]), "name": row["name"]}
    return None


def authenticate_incharge(email: str, password: str) -> dict | None:
    """Return incharge record dict on success, None on failure."""
    df = fetch_data(
        """SELECT incharge_id, campus_id, name, email, password_hash
           FROM Campus_Incharges WHERE email = :email""",
        {"email": email},
    )
    if df.empty:
        return None
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        return {"incharge_id": int(row["incharge_id"]),
                "campus_id": int(row["campus_id"]),
                "name": row["name"]}
    return None


def authenticate_stall(stall_id: int, password: str) -> dict | None:
    """Return stall record dict on success, None on failure."""
    df = fetch_data(
        """SELECT stall_id, campus_id, name, password_hash
           FROM Stalls WHERE stall_id = :sid""",
        {"sid": stall_id},
    )
    if df.empty:
        return None
    row = df.iloc[0]
    if _verify_password(password, row["password_hash"]):
        return {"stall_id": int(row["stall_id"]),
                "campus_id": int(row["campus_id"]),
                "name": row["name"]}
    return None


# ── Convenience getters used across pages ─────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def get_all_campuses() -> pd.DataFrame:
    return fetch_data("SELECT campus_id, name, real_location_lat, real_location_long FROM Campuses")


@st.cache_data(ttl=300, show_spinner=False)
def get_campus_name(campus_id: int) -> str:
    df = fetch_data("SELECT name FROM Campuses WHERE campus_id = :cid", {"cid": campus_id})
    return df.iloc[0]["name"] if not df.empty else "Unknown Campus"
