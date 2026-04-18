# Contributing to Campus Eats 🍔

Thank you for your interest in contributing to Campus Eats! We welcome bug reports, feature requests, and pull requests.

## 📋 Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Report issues privately if security-related

## 🐛 Reporting Bugs

### Before Submitting
- [ ] Search existing issues to avoid duplicates
- [ ] Check the latest version (might be fixed)
- [ ] Review [TROUBLESHOOTING.md](./SETUP.md#troubleshooting)

### When Submitting
1. **Title**: Clear, descriptive summary
2. **Description**: What did you try? What happened? What did you expect?
3. **Steps to Reproduce**: Exact steps to trigger the bug
4. **Environment**: Python version, OS, Streamlit version
5. **Logs**: Include error messages and tracebacks
6. **Screenshots**: If UI-related

**Example:**
```
Title: Login rate limiting blocks legitimate users after 5 attempts

Description: After failing to login 5 times, the system blocks login attempts 
for 15 minutes. This is too strict for users who forget passwords.

Steps:
1. Click "Global Admin"
2. Try invalid email 5 times
3. Try valid email - blocked with "Too many login attempts"

Environment:
- Python 3.9.0
- Windows 10
- Streamlit 1.45.1

Expected: Should provide password recovery option or increase limit to 10 attempts
```

## 💡 Feature Requests

### When Proposing
1. **Title**: Concise feature description
2. **Problem**: Why is this needed? What problem does it solve?
3. **Solution**: How should it work?
4. **Alternatives**: Other approaches considered?
5. **Impact**: How would this help users?

**Example:**
```
Title: Add email-based password recovery

Problem: Users who forget passwords are locked out for 15 minutes after 
5 failed attempts. There's no way to reset their password.

Solution: Add a "Forgot Password?" link that sends a password reset email 
with a temporary link good for 24 hours.

Impact: Improved user experience, reduced support requests for locked-out users
```

## 🔧 Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-username/campus-eats.git
cd "Campus Eats App"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest  # Optional: for code quality

# Setup pre-commit hooks
git config core.hooksPath .githooks  # If you create any
```

## 📝 Making Changes

### Code Style
- Follow PEP 8
- Use 4-space indentation
- Max line length: 100 characters
- Use type hints where possible

**Example:**
```python
# ✅ Good
def fetch_user_data(user_id: int) -> pd.DataFrame:
    """Fetch user data from database."""
    return fetch_data(
        "SELECT * FROM Students WHERE student_id = :uid",
        {"uid": user_id}
    )

# ❌ Bad
def fetch_user_data(id):
    return fetch_data("SELECT * FROM Students WHERE student_id = " + str(id))
```

### Security Standards
**ALL changes must follow [SECURITY_DEVELOPER_GUIDE.md](./SECURITY_DEVELOPER_GUIDE.md)**

Checklist for security:
- [ ] All inputs validated and sanitized
- [ ] Database queries parameterized
- [ ] Authorization checks included
- [ ] Error messages generic (no system info)
- [ ] Sensitive operations logged to audit trail
- [ ] No hardcoded secrets or credentials

### Git Workflow

1. **Create feature branch**
```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/issue-123
# or
git checkout -b docs/update-readme
```

2. **Make focused commits**
```bash
git add specific_file.py
git commit -m "Add feature X: brief description"
```

3. **Push to your fork**
```bash
git push origin feature/amazing-feature
```

4. **Create Pull Request**
   - Title: What does this change do?
   - Description: Why is this change needed?
   - Reference issues: "Fixes #123" or "Relates to #456"

## ✅ Pull Request Requirements

Your PR must include:

- [ ] **Clear title and description**
- [ ] **Reference to issue** (if applicable)
- [ ] **Updated tests** (if adding features)
- [ ] **Updated documentation** (if changing behavior)
- [ ] **No breaking changes** (or explicitly noted)
- [ ] **Follows code style** (black/flake8 compliant)
- [ ] **Security checklist** completed
- [ ] **No secret/sensitive data** in commits

### Security Checklist for PRs

Before submitting security-related changes:

```markdown
### Security Checklist
- [ ] Input validation added
- [ ] SQL injection protection confirmed
- [ ] XSS protection implemented
- [ ] Authorization checks included
- [ ] Error messages sanitized
- [ ] Audit logging added
- [ ] No secrets in code
- [ ] Follows SECURITY_DEVELOPER_GUIDE.md
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_auth.py

# Run with coverage
pytest --cov=. tests/
```

### Writing Tests

```python
# ✅ Good test
def test_rate_limiting_blocks_after_5_attempts():
    """Verify rate limiting blocks login after 5 failed attempts."""
    for i in range(5):
        record_failed_login("test@example.com")
    
    is_allowed, msg = check_rate_limit("test@example.com")
    assert not is_allowed
    assert "Too many login attempts" in msg

# ❌ Bad test
def test_login():
    login()  # Vague, no assertions
```

## 📚 Documentation

### Updating Docs

- **README.md**: Overview and quick start
- **SETUP.md**: Installation and setup
- **SECURITY_*.md**: Security-related information
- **Code docstrings**: Function documentation

### Documentation Style

```python
def fetch_stall_revenue(stall_id: int) -> pd.DataFrame:
    """
    Fetch revenue data for a specific stall.
    
    Only returns completed orders. Stall owners can only access
    their own stall data.
    
    Parameters
    ----------
    stall_id : int
        The ID of the stall
        
    Returns
    -------
    pd.DataFrame
        Columns: order_date, revenue, order_count
        
    Raises
    ------
    ValueError
        If stall_id is not numeric
    """
```

## 🚀 Release Process

### For Maintainers

1. **Update version**: Increment in version file
2. **Update CHANGELOG**: Document changes
3. **Tag release**: `git tag v1.0.0`
4. **Push tag**: `git push origin v1.0.0`
5. **Create release notes**: On GitHub releases page

### Version Format
Follow [Semantic Versioning](https://semver.org/):
- `1.0.0` - Major.Minor.Patch
- `1.0.0-beta.1` - Pre-release
- `1.0.0+build.1` - Build metadata

## 📞 Getting Help

- **Issues**: Ask questions in GitHub issues
- **Discussions**: Use GitHub discussions
- **Documentation**: Check guides in `/` directory
- **Security**: Report privately to maintainers

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors graph

## 📝 License

By contributing, you agree your contributions are licensed under the MIT License.

---

## Common Contribution Scenarios

### Adding a New Feature

1. Fork and create feature branch
2. Implement feature with security checks
3. Add tests
4. Update README/docs
5. Create PR with detailed description
6. Address review comments
7. Merge and celebrate! 🎉

### Fixing a Bug

1. Create issue with reproduction steps
2. Fork and create fix branch
3. Write test that reproduces bug
4. Fix the bug
5. Verify test passes
6. Create PR referencing issue
7. Merge after approval

### Improving Documentation

1. Edit markdown files directly in GitHub (if small change)
2. Or: Fork, edit, create PR
3. Verify formatting on GitHub preview
4. Keep tone consistent with existing docs
5. Merge after review

### Security Issues

⚠️ **Do NOT create public issues for security vulnerabilities**

Instead:
1. Email maintainers privately
2. Include detailed description
3. Allow time for fix before disclosure
4. Coordinate public disclosure timing

## 📊 Development Tips

### Useful Commands

```bash
# View git history
git log --oneline -10

# See changes before committing
git diff

# Check what you're about to push
git log origin/main..HEAD

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Format code with black
black .

# Check code style
flake8 *.py --max-line-length=100

# Run security check
pip check
bandit -r .
```

### Debugging

```bash
# Add to Home.py or any page
import sys
print("Debug:", variable_name, file=sys.stderr)

# Or use Streamlit's debug
st.write("Debug value:", debug_var)

# Check logs
streamlit run Home.py --logger.level=debug
```

---

**Thank you for contributing to Campus Eats!** 🙏

Every contribution helps make this project better for everyone.

