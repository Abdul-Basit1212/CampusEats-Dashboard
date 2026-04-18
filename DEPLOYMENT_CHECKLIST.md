# ✅ PRE-DEPLOYMENT CHECKLIST

Use this checklist before pushing to GitHub and deploying to production.

## 🔒 Security Pre-Deployment

### Secrets & Credentials
- [ ] `.env` file is NOT in git (check with `git status`)
- [ ] `.env.example` has placeholder values only
- [ ] Generated new API keys for production
- [ ] No API keys in any `.py` files
- [ ] No passwords hardcoded anywhere
- [ ] `DEMO_MODE=false` confirmed for production

### Environment Configuration
- [ ] `GEMINI_API_KEY` set to production key
- [ ] `DATABASE_URL` points to production database
- [ ] All environment variables documented in `.env.example`
- [ ] Reviewed all configuration options

### Code Security
- [ ] Ran through [SECURITY_DEVELOPER_GUIDE.md](./SECURITY_DEVELOPER_GUIDE.md)
- [ ] All inputs validated and sanitized
- [ ] All database queries parameterized
- [ ] No `unsafe_allow_html=True` in user-facing content
- [ ] Error handling uses `get_safe_error_message()`
- [ ] Audit logging in place for sensitive operations

### Dependencies
- [ ] All packages in `requirements.txt`
- [ ] No dev dependencies in production requirements
- [ ] Pinned versions where needed
- [ ] Checked for security vulnerabilities: `pip check`
- [ ] Updated to latest stable versions

## 🧪 Testing Pre-Deployment

### Functionality Tests
- [ ] Login works with admin account
- [ ] Login works with incharge account
- [ ] Login works with stall owner account
- [ ] Logout clears session properly
- [ ] Dashboard pages load without errors
- [ ] Sample data displays correctly

### Security Tests
- [ ] Rate limiting blocks after 5 failed attempts
- [ ] Session timeout works (30 minutes)
- [ ] Can't access other stalls' data
- [ ] Can't access other campuses' data
- [ ] Authorization checks work correctly
- [ ] Audit logs capture actions

### Performance Tests
- [ ] Dashboard loads in < 5 seconds
- [ ] Charts render without lag
- [ ] Large reports don't crash
- [ ] No memory leaks in extended use
- [ ] Database queries execute quickly

## 📝 Documentation Pre-Deployment

### README & Guides
- [ ] [README.md](./README.md) is comprehensive and current
- [ ] [SETUP.md](./SETUP.md) has clear setup instructions
- [ ] [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) documents all fixes
- [ ] [SECURITY_FIXES_SUMMARY.md](./SECURITY_FIXES_SUMMARY.md) explains changes
- [ ] [SECURITY_DEVELOPER_GUIDE.md](./SECURITY_DEVELOPER_GUIDE.md) ready for developers
- [ ] [GITHUB_DEPLOY.md](./GITHUB_DEPLOY.md) checked and verified

### Code Documentation
- [ ] All functions have docstrings
- [ ] Complex logic has comments
- [ ] `security.py` module documented
- [ ] Database functions explained
- [ ] API endpoints documented

### Project Files
- [ ] [LICENSE](./LICENSE) file present and correct
- [ ] [.gitignore](./.gitignore) properly configured
- [ ] [.env.example](./.env.example) has all required variables
- [ ] No TODO comments left in code

## 🚀 GitHub Pre-Deployment

### Repository Setup
- [ ] Repository name is clear and descriptive
- [ ] Repository description is accurate
- [ ] Topics tagged appropriately (python, streamlit, dashboard, etc.)
- [ ] README appears correctly on GitHub
- [ ] All documentation links work

### Git Configuration
- [ ] `.gitignore` verified (check what will be committed)
- [ ] Verify with: `git status`
  - [ ] `.env` should NOT be listed
  - [ ] `venv/` should NOT be listed
  - [ ] `__pycache__/` should NOT be listed
  - [ ] `*.db` should NOT be listed
  - [ ] `*.log` should NOT be listed

### Final Git Commands
- [ ] `git add .` - Stage all non-ignored files
- [ ] `git status` - Review what's being committed
- [ ] `git commit -m "Initial commit: Campus Eats Dashboard"` - Commit
- [ ] `git branch -M main` - Use main as default branch
- [ ] `git remote add origin https://github.com/username/campus-eats.git`
- [ ] `git push -u origin main` - Push to GitHub

## 🌐 Production Deployment

### Infrastructure
- [ ] Streamlit Cloud or similar HTTPS platform selected
- [ ] Domain configured (if applicable)
- [ ] HTTPS enabled and verified
- [ ] SSL certificate valid and auto-renewing

### Environment Setup
- [ ] Production environment variables set
- [ ] Database backups configured
- [ ] Monitoring tools in place
- [ ] Error logging configured
- [ ] Performance metrics tracking enabled

### Security Hardening
- [ ] HSTS headers configured
- [ ] Secure cookies enabled
- [ ] Rate limiting configured on server
- [ ] WAF (Web Application Firewall) considered
- [ ] Intrusion detection enabled

### Operational Readiness
- [ ] Incident response plan documented
- [ ] Backup and recovery procedures tested
- [ ] Team trained on deployment
- [ ] Runbook for common issues created
- [ ] Support contact information set up

## 📊 Monitoring Post-Deployment

### Health Checks
- [ ] Application is online and accessible
- [ ] Login authentication works
- [ ] Database queries execute
- [ ] API calls successful
- [ ] No error spikes in logs

### Security Monitoring
- [ ] Audit logs being collected
- [ ] Failed login attempts tracked
- [ ] No suspicious activity detected
- [ ] Rate limiting working
- [ ] Session timeouts functioning

### Performance Monitoring
- [ ] Response times acceptable
- [ ] No memory leaks detected
- [ ] Database performance normal
- [ ] API rate limits not exceeded
- [ ] System resources available

### User Experience
- [ ] Users can login successfully
- [ ] Dashboards load and display correctly
- [ ] Charts and visualizations work
- [ ] No data display errors
- [ ] Performance meets expectations

## 🔄 Rollback Plan

If issues occur after deployment:

```bash
# Stop current instance
# Revert to previous version
git revert <commit-hash>

# Or deploy from backup
# Follow your rollback procedure
```

### Rollback Testing
- [ ] Tested rollback process locally
- [ ] Backup database available
- [ ] Previous version builds successfully
- [ ] Rollback time documented

## 📋 Sign-Off

- [ ] **Security Review**: All critical issues resolved
- [ ] **Testing Complete**: All functionality verified
- [ ] **Documentation**: Comprehensive and current
- [ ] **Code Review**: Final review completed
- [ ] **Ready to Deploy**: All checklist items completed

---

## 🚀 Deployment Commands

When you're ready to deploy:

```bash
# Final verification
git status                    # Confirm what will be pushed
git log -1                    # Verify last commit

# Push to GitHub
git push -u origin main

# Deploy to Streamlit Cloud
# Go to https://share.streamlit.io
# Connect your repository
# Set environment variables
# Deploy

# Verify deployment
# Check app is accessible
# Verify authentication works
# Check audit logs
```

## 📞 Support

If deployment issues arise:

1. **Check logs**: Review application and server logs
2. **Review checklist**: Verify all steps were completed
3. **Consult guides**: Read [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) and [SECURITY_FIXES_SUMMARY.md](./SECURITY_FIXES_SUMMARY.md)
4. **Rollback if needed**: Use rollback procedures above

---

**Status**: ✅ Use this checklist for every deployment  
**Last Updated**: April 18, 2026  
**Version**: 1.0

