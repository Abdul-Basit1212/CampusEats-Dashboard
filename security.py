"""
security.py — CampusEats Security & Authorization Module

Provides:
- Session validation and immutability
- Rate limiting for login attempts
- Audit logging
- Input validation and sanitization
- Authorization checks
- Session timeout management
"""

import os
import json
import re
import hashlib
import hmac
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path

# ── CONFIGURATION ──────────────────────────────────────────────────────────
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
SESSION_TIMEOUT_MINUTES = 30
LOG_FILE = "audit_logs.json"
FAILED_LOGINS_FILE = ".failed_logins.json"

# ── EMAIL VALIDATION ───────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

def is_valid_email(email: str) -> bool:
    """Validate email format using RFC 5322 pattern."""
    return bool(EMAIL_REGEX.match(email.strip()))


# ── PASSWORD VALIDATION ────────────────────────────────────────────────────
def is_valid_password(password: str) -> bool:
    """
    Validate password strength:
    - At least 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def get_password_strength_feedback(password: str) -> str:
    """Return feedback on password weakness."""
    issues = []
    if len(password) < 8:
        issues.append("At least 8 characters")
    if not re.search(r'[A-Z]', password):
        issues.append("One uppercase letter (A-Z)")
    if not re.search(r'[0-9]', password):
        issues.append("One number (0-9)")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("One special character (!@#$%^&*...)")
    return f"Password needs: {', '.join(issues)}"


# ── INPUT SANITIZATION ─────────────────────────────────────────────────────
def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input:
    - Strip whitespace
    - Limit length
    - Escape HTML entities
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace
    value = value.strip()
    
    # Limit length
    value = value[:max_length]
    
    # Escape HTML entities
    value = (value.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;")
                  .replace("'", "&#x27;"))
    
    return value


def mask_sensitive_info(text: str, pattern: str = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}') -> str:
    """Mask sensitive information in logs (e.g., emails)."""
    return re.sub(pattern, "[REDACTED]", text)


# ── SESSION VALIDATION ─────────────────────────────────────────────────────
def validate_session() -> bool:
    """
    Re-validate session state on each page load.
    Returns True if session is valid, False otherwise.
    Protects against session hijacking/manipulation.
    """
    if not st.session_state.get("logged_in"):
        return False
    
    # Check required session keys exist
    required_keys = ["user_role", "user_name"]
    if not all(key in st.session_state for key in required_keys):
        _clear_session()
        return False
    
    # Validate role is valid
    valid_roles = ["admin", "incharge", "owner"]
    if st.session_state.user_role not in valid_roles:
        _clear_session()
        return False
    
    # Check session timeout
    if not _check_session_timeout():
        _clear_session()
        st.error("Session expired due to inactivity. Please login again.")
        return False
    
    # Update last activity time
    st.session_state.last_activity = datetime.now().timestamp()
    
    return True


def _check_session_timeout() -> bool:
    """Check if session has timed out due to inactivity."""
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now().timestamp()
        return True
    
    current_time = datetime.now().timestamp()
    last_activity = st.session_state.last_activity
    timeout_seconds = SESSION_TIMEOUT_MINUTES * 60
    
    if current_time - last_activity > timeout_seconds:
        return False
    
    return True


def _clear_session():
    """Clear all session state securely."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def get_session_timeout_warning() -> str:
    """Get remaining session timeout as string."""
    if "last_activity" not in st.session_state:
        return f"{SESSION_TIMEOUT_MINUTES}m"
    
    current_time = datetime.now().timestamp()
    last_activity = st.session_state.last_activity
    timeout_seconds = SESSION_TIMEOUT_MINUTES * 60
    remaining = timeout_seconds - (current_time - last_activity)
    
    if remaining < 0:
        return "0m"
    
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    
    return f"{minutes}m {seconds}s"


# ── AUTHORIZATION CHECKS ──────────────────────────────────────────────────
def authorize_stall_access(stall_id: int) -> bool:
    """
    Verify that current user can access the given stall.
    - Stall owners can only access their own stall
    - Campus incharges can access stalls in their campus
    - Admins can access any stall
    """
    if not validate_session():
        return False
    
    user_role = st.session_state.user_role
    
    if user_role == "admin":
        return True  # Admins can access all stalls
    
    if user_role == "owner":
        # Stall owner can only access their own stall
        return int(st.session_state.entity_id) == int(stall_id)
    
    if user_role == "incharge":
        # Campus incharge can access stalls in their campus
        # This would require checking database, done in data fetchers
        return True
    
    return False


def authorize_campus_access(campus_id: int) -> bool:
    """
    Verify that current user can access the given campus.
    - Stall owners can access campus of their stall
    - Campus incharges can only access their campus
    - Admins can access any campus
    """
    if not validate_session():
        return False
    
    user_role = st.session_state.user_role
    
    if user_role == "admin":
        return True  # Admins can access all campuses
    
    if user_role == "incharge":
        return int(st.session_state.campus_id) == int(campus_id)
    
    if user_role == "owner":
        # Owner can access their stall's campus
        return int(st.session_state.campus_id) == int(campus_id)
    
    return False


# ── RATE LIMITING ──────────────────────────────────────────────────────────
def _load_failed_logins() -> dict:
    """Load failed login attempts from file."""
    if not os.path.exists(FAILED_LOGINS_FILE):
        return {}
    
    try:
        with open(FAILED_LOGINS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def _save_failed_logins(data: dict):
    """Save failed login attempts to file."""
    try:
        with open(FAILED_LOGINS_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass  # Silently fail if can't save


def _get_identifier_hash(identifier: str) -> str:
    """Get hash of identifier for rate limiting (don't store plaintext)."""
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def check_rate_limit(identifier: str) -> tuple[bool, str]:
    """
    Check if identifier is rate limited.
    Returns: (is_allowed, message)
    """
    now = datetime.now().timestamp()
    identifier_hash = _get_identifier_hash(identifier)
    
    failed_logins = _load_failed_logins()
    
    if identifier_hash not in failed_logins:
        return True, ""
    
    attempts_data = failed_logins[identifier_hash]
    attempt_times = attempts_data.get("times", [])
    
    # Remove old attempts outside the window
    valid_attempts = [t for t in attempt_times if now - t < RATE_LIMIT_WINDOW]
    
    if len(valid_attempts) >= RATE_LIMIT_ATTEMPTS:
        # User is rate limited
        oldest_attempt = min(valid_attempts)
        time_until_reset = RATE_LIMIT_WINDOW - (now - oldest_attempt)
        minutes = int(time_until_reset / 60) + 1
        message = f"Too many login attempts. Try again in {minutes} minute(s)."
        return False, message
    
    return True, ""


def record_failed_login(identifier: str):
    """Record a failed login attempt."""
    now = datetime.now().timestamp()
    identifier_hash = _get_identifier_hash(identifier)
    
    failed_logins = _load_failed_logins()
    
    if identifier_hash not in failed_logins:
        failed_logins[identifier_hash] = {"times": [], "ip": ""}
    
    failed_logins[identifier_hash]["times"].append(now)
    
    # Keep only recent attempts (clean up old ones)
    failed_logins[identifier_hash]["times"] = [
        t for t in failed_logins[identifier_hash]["times"]
        if now - t < RATE_LIMIT_WINDOW * 2
    ]
    
    _save_failed_logins(failed_logins)
    
    # Log suspicious activity
    log_audit("failed_login", f"Failed login for: {identifier_hash}")


def clear_failed_logins(identifier: str):
    """Clear failed login attempts for successful login."""
    identifier_hash = _get_identifier_hash(identifier)
    failed_logins = _load_failed_logins()
    
    if identifier_hash in failed_logins:
        del failed_logins[identifier_hash]
        _save_failed_logins(failed_logins)


# ── AUDIT LOGGING ──────────────────────────────────────────────────────────
def log_audit(action: str, details: str = "", user_role: str = None, entity_id: str = None):
    """
    Log audit trail for security monitoring.
    Stores action, timestamp, user info for accountability.
    """
    if user_role is None:
        user_role = st.session_state.get("user_role", "anonymous")
    
    if entity_id is None:
        entity_id = st.session_state.get("entity_id", "N/A")
    
    # Sanitize details to remove sensitive info
    details = mask_sensitive_info(details)
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "user_role": user_role,
        "entity_id": entity_id,
    }
    
    try:
        # Append to log file
        entries = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                try:
                    entries = json.load(f)
                except:
                    entries = []
        
        entries.append(audit_entry)
        
        # Keep only last 10000 entries to prevent file from growing too large
        if len(entries) > 10000:
            entries = entries[-10000:]
        
        with open(LOG_FILE, 'w') as f:
            json.dump(entries, f)
    except Exception as e:
        print(f"Audit logging error: {e}")


def get_audit_logs(limit: int = 100) -> list:
    """Retrieve recent audit logs (admin only)."""
    if st.session_state.get("user_role") != "admin":
        return []
    
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r') as f:
            entries = json.load(f)
        
        # Return most recent entries first
        return entries[-limit:][::-1]
    except:
        return []


# ── ERROR MESSAGE SANITIZATION ────────────────────────────────────────────
def get_safe_error_message(error: Exception) -> str:
    """
    Convert exception to safe error message that doesn't leak system info.
    Full error is logged separately for debugging.
    """
    error_str = str(error).lower()
    
    # Log full error for debugging
    log_audit("error", str(error))
    
    # Return generic message
    if "database" in error_str or "sql" in error_str:
        return "A database error occurred. Please try again later."
    elif "connection" in error_str:
        return "Connection error. Please check your internet and try again."
    elif "timeout" in error_str:
        return "Request timed out. Please try again."
    else:
        return "An unexpected error occurred. Please try again or contact support."
