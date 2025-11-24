# 🔐 GitHub Secrets Setup Guide

This guide shows you how to add API keys to GitHub Secrets for CI/CD automation.

---

## ⚠️ **Linter Warnings in `ci.yml`**

You may see warnings like:
```
Context access might be invalid: XAI_API_KEY
Context access might be invalid: ODDS_API_KEY
```

**This is expected!** These warnings appear because the secrets haven't been added to GitHub yet. They will disappear once you add the secrets following the steps below.

---

## 🔑 **Required Secrets**

### **For Automated Edge Discovery** (Weekly runs):
1. **`XAI_API_KEY`** - Your xAI Grok API key
   - Get from: https://x.ai/api
   - Used for: AI-powered hypothesis generation

2. **`ODDS_API_KEY`** - Your The Odds API key
   - Get from: https://the-odds-api.com/
   - Used for: Live betting lines and odds

---

## 📝 **How to Add Secrets**

### **Step 1: Navigate to Repository Settings**

Go to:
```
https://github.com/EAGLE605/nfl-betting-system/settings/secrets/actions
```

Or manually:
1. Click on **Settings** tab (top of repository)
2. In left sidebar, click **Secrets and variables** → **Actions**
3. You'll see the "Actions secrets" page

### **Step 2: Add Each Secret**

For each secret:

1. Click **"New repository secret"** button
2. Enter the **Name** (exactly as shown below)
3. Paste the **Value** (your actual API key)
4. Click **"Add secret"**

### **Step 3: Verify Secrets Are Added**

After adding, you should see:
```
✓ XAI_API_KEY (Updated X time ago)
✓ ODDS_API_KEY (Updated X time ago)
```

---

## 🔒 **Secret Names and Values**

### **Secret #1: XAI_API_KEY**
```
Name: XAI_API_KEY
Value: xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Where to get**:
1. Go to https://x.ai/api
2. Sign in with your account
3. Navigate to API keys section
4. Copy your API key

### **Secret #2: ODDS_API_KEY**
```
Name: ODDS_API_KEY
Value: your_odds_api_key_here
```

**Where to get**:
1. Go to https://the-odds-api.com/
2. Sign up for free account (500 requests/month)
3. Go to dashboard
4. Copy your API key

---

## 🧪 **Testing Your Secrets**

### **Option 1: Trigger Manual Workflow Run**

1. Go to **Actions** tab
2. Select **"NFL Betting System CI/CD"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. Check the **"Weekly Edge Discovery"** job runs successfully

### **Option 2: Wait for Scheduled Run**

The workflow runs automatically every Monday at 6 AM UTC. Check the next morning.

### **Option 3: Make a Test Commit**

```bash
# Add a comment to README
echo "# Testing CI/CD" >> README.md
git add README.md
git commit -m "test: Verify CI/CD pipeline"
git push
```

Then check the **Actions** tab to see if tests run.

---

## 🚫 **Optional Secrets** (Not Required for CI/CD)

These secrets are **only needed** if you want email/SMS notifications:

### **Email Notifications** (Gmail SMTP):
```
EMAIL_USER: your_email@gmail.com
EMAIL_PASSWORD: your_gmail_app_password
EMAIL_RECIPIENT: recipient@email.com
```

### **SMS Notifications** (Twilio):
```
TWILIO_ACCOUNT_SID: your_twilio_account_sid
TWILIO_AUTH_TOKEN: your_twilio_auth_token
TWILIO_PHONE_FROM: +1234567890
TWILIO_PHONE_TO: +1234567890
```

---

## ❓ **FAQ**

### **Q: Why do I see linter warnings about secrets?**
A: GitHub Actions linter warns about undefined secrets. This is normal. The warnings will disappear once you add the secrets. The workflow is designed to handle missing secrets gracefully with `continue-on-error: true`.

### **Q: What happens if I don't add secrets?**
A: The CI/CD pipeline will still work! Only the **"Weekly Edge Discovery"** job requires secrets. The test, lint, and security jobs will run normally. The edge discovery job will be skipped if secrets are missing.

### **Q: Are my secrets safe?**
A: Yes! GitHub Secrets are:
- Encrypted at rest
- Never exposed in logs (shown as `***`)
- Only accessible to workflows in this repository
- Can be rotated/deleted at any time

### **Q: Can I use different API keys locally vs CI/CD?**
A: Yes! Local development uses `config/api_keys.env` (gitignored), while CI/CD uses GitHub Secrets. They're completely separate.

### **Q: How do I rotate/update a secret?**
A:
1. Go to repository Settings → Secrets → Actions
2. Click on the secret name
3. Click **"Update secret"**
4. Paste new value
5. Click **"Update secret"**

### **Q: How do I delete a secret?**
A:
1. Go to repository Settings → Secrets → Actions
2. Click on the secret name
3. Click **"Remove secret"**
4. Confirm deletion

---

## 🎯 **What Happens After Adding Secrets**

### **Immediate**:
- ✅ Linter warnings in `ci.yml` will disappear
- ✅ Weekly edge discovery can run automatically
- ✅ AI-powered hypothesis generation enabled

### **Every Monday at 6 AM UTC**:
- ✅ Downloads latest NFL data
- ✅ Runs statistical edge discovery
- ✅ Uses Grok AI to generate new hypotheses
- ✅ Uploads results as workflow artifacts

### **On Every Push**:
- ✅ Runs test suite
- ✅ Checks code quality
- ✅ Scans for security vulnerabilities
- ✅ (Edge discovery only runs on schedule)

---

## 📊 **Monitoring Your Workflow**

### **View Workflow Runs**:
```
https://github.com/EAGLE605/nfl-betting-system/actions
```

### **Download Edge Discovery Results**:
1. Go to Actions tab
2. Click on a workflow run (with green checkmark)
3. Scroll to **"Artifacts"** section
4. Download **"edge-discovery-results"**
5. Extract and review:
   - `bulldog_edges_discovered.csv`
   - `edges_database.json`

---

## 🔗 **Quick Links**

- **Add Secrets**: https://github.com/EAGLE605/nfl-betting-system/settings/secrets/actions
- **View Actions**: https://github.com/EAGLE605/nfl-betting-system/actions
- **xAI API**: https://x.ai/api
- **The Odds API**: https://the-odds-api.com/
- **GitHub Secrets Docs**: https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

## ✅ **Verification Checklist**

- [ ] Navigate to repository settings
- [ ] Click Secrets and variables → Actions
- [ ] Add `XAI_API_KEY` secret
- [ ] Add `ODDS_API_KEY` secret
- [ ] Verify secrets show in list
- [ ] Trigger manual workflow run (or wait for Monday)
- [ ] Check Actions tab for successful run
- [ ] Download and review artifacts
- [ ] Linter warnings disappear in `ci.yml`

---

**Need help?** Open an issue in the repository or check the [GitHub Docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

