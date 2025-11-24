# Security Policy & Best Practices

## 🔐 Security Status: SECURED

**Last Security Audit**: November 24, 2025  
**Status**: All sensitive data removed from git history and properly protected

---

## 🚨 Critical Security Measures Implemented

### 1. API Key Protection

✅ **FIXED**: All API keys have been:
- Removed from git history using BFG Repo Cleaner
- Moved to `config/api_keys.env` (gitignored)
- Protected by multiple `.gitignore` rules

### 2. Environment Files Protected

The following files are **NEVER** committed to git:
- `config/api_keys.env` - Contains all API keys
- `.env` - Any environment-specific configuration
- `*.env` - All environment files

### 3. Git History Cleaned

API keys that were previously exposed have been:
- Removed from all commits using BFG Repo Cleaner
- Purged from git reflog
- Cleaned with aggressive garbage collection

---

## 📋 API Keys Used in This Project

| Service | Key Variable | Where to Get It | Required? |
|---------|--------------|-----------------|-----------|
| The Odds API | `ODDS_API_KEY` | https://the-odds-api.com/ | ✅ Yes |
| xAI Grok API | `XAI_API_KEY` | https://x.ai/api | ⚠️ Optional |
| Odds Widget | `ODDS_WIDGET_KEY` | https://the-odds-api.com/ | ⚠️ Optional |
| Email (Gmail) | `EMAIL_USER`, `EMAIL_PASSWORD` | Gmail App Passwords | ⚠️ Optional |
| Twilio SMS | `TWILIO_*` | https://www.twilio.com/ | ⚠️ Optional |

---

## 🔧 Setup Instructions for New Users

### Step 1: Copy the Template

```powershell
Copy-Item config/api_keys.env.template config/api_keys.env
```

### Step 2: Add Your API Keys

Edit `config/api_keys.env` and replace the placeholder values:

```bash
# REQUIRED
ODDS_API_KEY="your_actual_key_here"

# OPTIONAL (for enhanced features)
XAI_API_KEY="your_xai_key_here"
ODDS_WIDGET_KEY="your_widget_key_here"
```

### Step 3: Verify Protection

```powershell
# This should output: .gitignore:77:*.env	config/api_keys.env
git check-ignore -v config/api_keys.env
```

If you see output like above, your file is protected! ✅

---

## 🚫 NEVER Do These Things

### ❌ Don't Hardcode API Keys

**BAD:**
```python
API_KEY = '7f5005117f0b98ea00ef64e2cb4b26a4'  # NEVER DO THIS!
```

**GOOD:**
```python
import os
from dotenv import load_dotenv

load_dotenv('config/api_keys.env')
API_KEY = os.getenv('ODDS_API_KEY')
```

### ❌ Don't Commit Environment Files

**BAD:**
```powershell
git add config/api_keys.env
git commit -m "Add API keys"  # NEVER DO THIS!
```

**GOOD:**
```powershell
# config/api_keys.env is automatically ignored
# Only commit the template:
git add config/api_keys.env.template
git commit -m "Update API key template"
```

### ❌ Don't Share Keys in Documentation

Never include real API keys in:
- README files
- Documentation
- Code comments
- Issue reports
- Pull requests

---

## 🆘 Emergency: I Accidentally Committed a Secret!

If you accidentally commit an API key, **DO THIS IMMEDIATELY**:

### Step 1: Revoke the Compromised Key

**CRITICAL**: Before cleaning git history, revoke the exposed key:

- **The Odds API**: https://the-odds-api.com/ → Dashboard → Regenerate Key
- **xAI Grok**: https://x.ai/ → API Keys → Revoke & Create New
- **Twilio**: https://www.twilio.com/console → Revoke auth token

### Step 2: Clean Git History

We've provided a cleanup script:

```powershell
# 1. Install BFG Repo Cleaner (if not already installed)
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar" -OutFile "bfg.jar"

# 2. Create a file with strings to remove
echo "your_exposed_key_here" > secrets.txt

# 3. Run BFG
java -jar bfg.jar --replace-text secrets.txt --no-blob-protection

# 4. Clean up git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push (WARNING: destructive!)
git push --force --all
git push --force --tags

# 6. Delete temporary files
Remove-Item bfg.jar, secrets.txt
```

### Step 3: Notify GitHub

If pushed to GitHub, you should also contact GitHub Support to purge the cached commits.

---

## 🔍 Security Audit Checklist

Run this checklist periodically:

```powershell
# 1. Check for exposed secrets in current files
git grep -i "api_key\|secret\|password\|token" | Select-String -NotMatch "getenv|env\[|placeholder|template|example"

# 2. Verify gitignore is working
git check-ignore -v config/api_keys.env

# 3. Check for accidentally tracked env files
git ls-files | Select-String "\.env$|api_keys\.env"

# 4. Scan git history for secrets (use gitleaks or trufflehog)
# Install: pip install truffleHog
# Run: trufflehog filesystem . --json
```

**Expected Results**:
- Grep: Only template files and code using `os.getenv()`
- Check-ignore: Should show config/api_keys.env is ignored
- Ls-files: Should only show `.env.template` files
- TruffleHog: No secrets detected

---

## 🛡️ Additional Security Best Practices

### 1. Use Read-Only Keys When Possible

For APIs that support it, create read-only or restricted keys:
- Limit by IP address
- Set usage quotas
- Restrict to specific endpoints

### 2. Rotate Keys Regularly

- **The Odds API**: Rotate every 6 months or after team changes
- **xAI Grok**: Rotate after any suspected exposure
- **Twilio**: Use separate keys for dev/prod

### 3. Monitor API Usage

Watch for unusual activity:
- Unexpected API quota usage
- Requests from unknown IPs
- Failed authentication attempts

### 4. Use Environment-Specific Keys

```bash
# Development keys (lower limits)
ODDS_API_KEY_DEV="dev_key_here"

# Production keys (full access)
ODDS_API_KEY_PROD="prod_key_here"
```

---

## 📚 Security Tools & Resources

### Recommended Tools

1. **BFG Repo Cleaner** - Remove secrets from git history  
   https://rtyley.github.io/bfg-repo-cleaner/

2. **TruffleHog** - Scan for secrets in git history  
   ```powershell
   pip install trufflehog
   trufflehog filesystem . --json
   ```

3. **GitGuardian** - Real-time secret detection  
   https://www.gitguardian.com/

4. **git-secrets** - Prevent secrets from being committed  
   https://github.com/awslabs/git-secrets

### GitHub Security Features

Enable these in your repository:

- ✅ **Secret Scanning**: Settings → Security → Secret scanning
- ✅ **Push Protection**: Blocks commits with detected secrets
- ✅ **Dependabot Alerts**: Monitors dependency vulnerabilities
- ✅ **Security Advisories**: Private vulnerability reporting

---

## 🤝 Contributing Securely

If you're contributing to this project:

1. **Never commit real API keys** - Use the template
2. **Review your changes** before committing:
   ```powershell
   git diff --cached
   ```
3. **Use test/mock keys** in examples:
   ```python
   API_KEY = "test_key_12345"  # Example only
   ```
4. **Report security issues privately** - Don't open public issues

---

## 📞 Security Contact

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email the repository owner privately
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

---

## 🎯 Security Incident History

### November 24, 2025 - API Keys Exposed & Remediated

**Issue**: API keys were hardcoded in `scripts/test_odds_api.py` and committed to git history.

**Impact**: 
- The Odds API key: `7f50...26a4` (REVOKED)
- xAI Grok API key: `xai-qs0j...lvuK` (REVOKED)
- Odds Widget key: `wk_03ab...ed74` (REVOKED)

**Resolution**:
1. ✅ All keys removed from git history using BFG Repo Cleaner
2. ✅ Keys moved to gitignored `config/api_keys.env`
3. ✅ Git history cleaned and force-pushed
4. ⚠️ **USERS MUST**: Revoke old keys and generate new ones

**Preventive Measures**:
- Added pre-commit hooks (planned)
- Updated documentation
- Created this security policy

---

## ✅ Current Security Status

| Check | Status | Last Verified |
|-------|--------|---------------|
| API keys removed from git history | ✅ PASS | 2025-11-24 |
| .gitignore properly configured | ✅ PASS | 2025-11-24 |
| No hardcoded secrets in code | ✅ PASS | 2025-11-24 |
| Environment template provided | ✅ PASS | 2025-11-24 |
| Documentation updated | ✅ PASS | 2025-11-24 |

---

## 📖 Additional Reading

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

---

**Remember**: Security is not a one-time task, it's an ongoing practice! 🔒

