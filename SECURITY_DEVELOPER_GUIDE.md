# 🔐 DEVELOPER SECURITY REFERENCE GUIDE

## Quick Security Checklist for New Code

When adding new features to Campus Eats App, follow these security guidelines:

### ✅ Authentication & Authorization

```python
# ❌ WRONG - No authorization check
@st.cache_data
def get_stall_data(stall_id: int):
    return fetch_data(f"SELECT * FROM Stalls WHERE stall_id = {stall_id}")

# ✅ CORRECT - Authorize access first
from security import authorize_stall_access

@st.cache_data
def get_stall_data(stall_id: int):
    if not authorize_stall_access(stall_id):
        st.error("Unauthorized")
        return pd.DataFrame()
    return fetch_data(
        "SELECT * FROM Stalls WHERE stall_id = :sid",
        {"sid": stall_id}
    )
```

### ✅ Input Validation

```python
# ❌ WRONG - No validation
email = st.text_input("Email")
result = authenticate_admin(email, password)

# ✅ CORRECT - Validate input first
from security import is_valid_email, sanitize_input

email = sanitize_input(st.text_input("Email"))
if not is_valid_email(email):
    st.error("Invalid email format")
else:
    result = authenticate_admin(email, password)
```

### ✅ Session Validation

```python
# ❌ WRONG - No session validation
if st.session_state.get("logged_in"):
    show_data()

# ✅ CORRECT - Validate session on page load
from security import validate_session

if not validate_session():
    st.switch_page("Home.py")
    st.stop()

show_data()
```

### ✅ Error Handling

```python
# ❌ WRONG - Exposes database details
try:
    result = fetch_data(query)
except Exception as e:
    st.error(f"Database error: {e}")  # Leaks info

# ✅ CORRECT - Safe error message
from security import get_safe_error_message

try:
    result = fetch_data(query)
except Exception as e:
    error_msg = get_safe_error_message(e)
    st.error(error_msg)  # Generic message
```

### ✅ Audit Logging

```python
# ❌ WRONG - No logging
sensitive_operation()

# ✅ CORRECT - Log important actions
from security import log_audit

log_audit("data_export", f"Exported {len(data)} records")
sensitive_operation()
```

### ✅ Parameterized Queries

```python
# ❌ WRONG - SQL Injection vulnerability
df = fetch_data(f"SELECT * FROM Students WHERE campus_id = {campus_id}")

# ✅ CORRECT - Parameterized query
df = fetch_data(
    "SELECT * FROM Students WHERE campus_id = :cid",
    {"cid": campus_id}
)
```

---

## Security Module API Reference

### Authentication & Authorization

```python
from security import (
    validate_session,           # Returns bool
    authorize_stall_access,     # (stall_id) -> bool
    authorize_campus_access,    # (campus_id) -> bool
)

# Usage
if not validate_session():
    st.switch_page("Home.py")
    st.stop()

if not authorize_stall_access(stall_id):
    st.error("You don't have access to this stall")
```

### Input Validation & Sanitization

```python
from security import (
    is_valid_email,                    # (email) -> bool
    is_valid_password,                 # (password) -> bool
    get_password_strength_feedback,    # (password) -> str
    sanitize_input,                    # (value, max_length) -> str
    mask_sensitive_info,               # (text, pattern) -> str
)

# Usage
if not is_valid_email(email):
    st.error("Invalid email format")

password = sanitize_input(st.text_input("Password", type="password"))
```

### Rate Limiting & Login Protection

```python
from security import (
    check_rate_limit,       # (identifier) -> (bool, str)
    record_failed_login,    # (identifier) -> None
    clear_failed_logins,    # (identifier) -> None
)

# Usage (done in database.py)
is_allowed, message = check_rate_limit(email)
if not is_allowed:
    st.error(message)
    return None
```

### Audit Logging

```python
from security import (
    log_audit,           # (action, details, user_role, entity_id) -> None
    get_audit_logs,      # (limit) -> list
)

# Usage
log_audit("user_export", "Exported student list", "admin", "1")
# Later, view logs
logs = get_audit_logs(100)  # Last 100 entries
```

### Error Handling

```python
from security import (
    get_safe_error_message,  # (exception) -> str
)

# Usage
try:
    data = fetch_data(query)
except Exception as e:
    safe_msg = get_safe_error_message(e)
    st.error(safe_msg)  # Show user-friendly message
    log_audit("error", str(e))  # Log full error
```

---

## Database Security Best Practices

### Always Use Parameterized Queries

```python
# ✅ CORRECT
from database import fetch_data

df = fetch_data(
    """
    SELECT * FROM Orders 
    WHERE stall_id = :stall_id 
      AND order_time >= :start_date
    """,
    {"stall_id": stall_id, "start_date": "2024-01-01"}
)

# ✅ ALSO CORRECT - Using SQLAlchemy text()
from sqlalchemy import text
df = pd.read_sql(
    text("SELECT * FROM Orders WHERE stall_id = :sid"),
    connection,
    params={"sid": stall_id}
)
```

### Never Use String Formatting

```python
# ❌ WRONG - SQL Injection vulnerability
query = f"SELECT * FROM Orders WHERE stall_id = {stall_id}"

# ❌ WRONG - Still vulnerable with format()
query = "SELECT * FROM Orders WHERE stall_id = {}".format(stall_id)

# ❌ WRONG - Still vulnerable with f-strings
query = f"SELECT * FROM Orders WHERE stall_id = {stall_id}"
```

---

## Common Security Patterns

### Pattern 1: Protected Page

```python
import streamlit as st
from security import validate_session
from database import fetch_data

st.set_page_config(page_title="My Page", page_icon="📄")

# 1. Validate session first
if not validate_session():
    st.warning("Session invalid. Please login.")
    st.switch_page("Home.py")
    st.stop()

# 2. Check role
if st.session_state.user_role != "admin":
    st.error("Admin access required")
    st.stop()

# 3. Now safe to show content
st.title("Admin Dashboard")
```

### Pattern 2: Scoped Data Access

```python
from security import authorize_stall_access

@st.cache_data(ttl=300)
def get_stall_revenue(stall_id: int):
    # 1. Authorize access
    if not authorize_stall_access(stall_id):
        return pd.DataFrame()
    
    # 2. Fetch with parameterized query
    return fetch_data(
        "SELECT * FROM Orders WHERE stall_id = :sid",
        {"sid": stall_id}
    )

# Usage
stall_id = st.session_state.entity_id  # Their stall
data = get_stall_revenue(stall_id)
```

### Pattern 3: Safe Form Input

```python
from security import is_valid_email, sanitize_input, log_audit

with st.form("my_form"):
    email = sanitize_input(st.text_input("Email"))
    message = sanitize_input(st.text_area("Message"), max_length=5000)
    
    if st.form_submit_button("Submit"):
        if not is_valid_email(email):
            st.error("Invalid email")
        else:
            # Process form
            log_audit("form_submission", f"Email: {email[:10]}...")
            st.success("Done!")
```

---

## Logging & Debugging

### Enable Audit Logs in Admin Page

```python
from security import get_audit_logs

if st.session_state.user_role == "admin":
    with st.expander("🔍 Audit Logs (Admin Only)"):
        logs = get_audit_logs(50)  # Last 50 entries
        st.json(logs)
```

### View Failed Logins

```python
import json

try:
    with open(".failed_logins.json", "r") as f:
        data = json.load(f)
    st.write(data)
except:
    st.write("No failed logins recorded")
```

---

## Security Testing

### Test Rate Limiting

```python
# Simulate 6 failed login attempts (should be blocked)
from security import record_failed_login, check_rate_limit

for i in range(6):
    record_failed_login("test@example.com")

is_allowed, msg = check_rate_limit("test@example.com")
assert not is_allowed  # Should be True (blocked)
print(msg)  # Should show "Too many login attempts..."
```

### Test Input Validation

```python
from security import is_valid_email, is_valid_password

# Email validation
assert is_valid_email("user@example.com")  # True
assert not is_valid_email("invalid.email")  # False

# Password validation
assert is_valid_password("MyPass123!")  # True
assert not is_valid_password("weak")  # False
```

---

## Configuration

All security settings are in `security.py`:

```python
# Rate Limiting
RATE_LIMIT_ATTEMPTS = 5           # Max attempts
RATE_LIMIT_WINDOW = 900           # Per 15 minutes

# Session
SESSION_TIMEOUT_MINUTES = 30      # Idle timeout

# Files
LOG_FILE = "audit_logs.json"      # Audit log location
FAILED_LOGINS_FILE = ".failed_logins.json"  # Login attempts
```

### Adjusting Settings

To change rate limiting:
```python
# In security.py
RATE_LIMIT_ATTEMPTS = 10          # Allow 10 attempts
RATE_LIMIT_WINDOW = 1800          # Per 30 minutes
```

---

## Troubleshooting

### Issue: "Session expired due to inactivity"
**Cause:** User idle for 30+ minutes  
**Solution:** Adjust `SESSION_TIMEOUT_MINUTES` in `security.py` or refresh page to continue

### Issue: "Too many login attempts"
**Cause:** 5+ failed attempts in 15 minutes  
**Solution:** Wait 15 minutes or delete `.failed_logins.json`

### Issue: "Invalid email format"
**Cause:** Email doesn't match RFC 5322 pattern  
**Solution:** Use valid email like `user@example.com`

### Issue: "Access denied. You don't have permission"
**Cause:** Trying to access resource not owned  
**Solution:** Only access resources you own (your stall/campus)

---

## Resources

- **Security Audit:** See `SECURITY_AUDIT.md`
- **Fixes Summary:** See `SECURITY_FIXES_SUMMARY.md`
- **Main Repo:** Follow `.gitignore` rules
- **Deployment:** See `README.md` for production deployment

---

**Last Updated:** April 18, 2026  
**Version:** 1.0  
**For Questions:** Review comments in `security.py`

