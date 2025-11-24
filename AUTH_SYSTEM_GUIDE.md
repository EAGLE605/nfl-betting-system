# 🔐 Authentication System Guide

## 🎯 Quick Summary

Your NFL Edge Finder now has **enterprise-grade authentication**:

- ✅ **Admin Access**: b_flink@hotmail.com (Password: Stevie2019!)
- ✅ **Password Reset**: Email-based reset for all users
- ✅ **2FA Support**: Optional two-factor authentication
- ✅ **Role-Based Access**: Admin vs Regular users
- ✅ **Nice Features**: Clean, simple UI for everyone

---

## 🚀 Quick Start

### Run the Authenticated App

```bash
# Windows
start_dashboard_auth.bat

# Mac/Linux
./start_dashboard_auth.sh

# Or manually
streamlit run dashboard/app_complete.py
```

**Opens at**: http://localhost:8501

---

## 👤 User Roles

### 🔑 **ADMIN ACCESS** (b_flink@hotmail.com ONLY)

**Login Credentials**:
- Email: `b_flink@hotmail.com`
- Username: `admin`
- Password: `Stevie2019!`

**Admin Features**:
- ✅ All regular user features
- ✅ 🤖 Bulldog AI controls
- ✅ 🎓 One-click model retraining
- ✅ 📊 Feature management
- ✅ 🔄 Data pipeline controls
- ✅ ⚡ Automation scheduling
- ✅ 🛠️ System configuration
- ✅ 👥 View all users (future)

### 👤 **REGULAR USERS** (Everyone Else)

**Features for Everyone**:
- ✅ 🎯 **Today's Picks**: AI-powered betting recommendations
- ✅ 📊 **Performance Tracking**: Win rate, ROI, profit/loss
- ✅ 💰 **Bankroll Manager**: Smart bet sizing recommendations
- ✅ ⚙️ **Account Settings**: Profile, security, preferences

---

## 📋 Features Breakdown

### For ALL Users (Simple & Logical)

#### 🎯 **My Picks Page**
- **What it does**: Shows 3-5 best bets for today
- **Features**:
  - Win probability for each pick
  - Edge calculation (+X% expected value)
  - Recommended bet size (based on your bankroll)
  - Reasoning why the bet is good
  - One-tap bet tracking
- **Why it's nice**: Clean cards, easy to understand, actionable

#### 📊 **Performance Page**
- **What it does**: Track all your bets and results
- **Features**:
  - Win rate, total profit, ROI metrics
  - Recent bet history
  - Update bet status (pending → won/lost)
  - Automatic profit calculation
- **Why it's nice**: See exactly how you're doing at a glance

#### 💰 **Bankroll Page**
- **What it does**: Manage your betting bankroll
- **Features**:
  - Update current bankroll
  - Choose risk profile (small/medium/large)
  - Get recommended bet sizes
  - See risk of ruin estimates
- **Why it's nice**: Personalized to your situation

#### ⚙️ **Settings Page**
- **What it does**: Control your account
- **Features**:
  - Update profile info
  - Change password
  - Enable/disable 2FA
  - Set notification preferences
  - Adjust minimum edge/probability filters
- **Why it's nice**: Full control, nothing hidden

---

### For ADMIN Only (Advanced Controls)

#### 🤖 **Bulldog AI Tab**
- Enable/disable self-improving AI
- Configure exploration rate
- Run edge discovery
- View recent discoveries
- Deploy new strategies

#### 🎓 **Model Training Tab**
- One-click training (Quick/Deep/Tune)
- Select seasons and features
- Adjust hyperparameters
- Compare model performance
- Schedule auto-retraining

#### 📊 **Features Tab**
- Enable/disable features
- View feature importance
- Run genetic feature search
- Correlation analysis

#### 🔄 **Data Pipeline Tab**
- Download latest data
- Force refresh cache
- Clean old data
- Run data audit

#### ⚡ **Automation Tab**
- View scheduled tasks
- Enable/disable automation
- Run tasks manually
- Configure schedules

#### 🛠️ **System Tab**
- Manage API keys
- Backup database
- Export models/reports
- Advanced configuration

---

## 🔑 Authentication Features

### 📧 **Password Reset**

**How it works**:
1. Click "Reset Password" tab on login page
2. Enter your email
3. Get reset link (displayed on screen)
4. Click link, set new password
5. Done! Sign in with new password

**Note**: In production, this sends actual emails. For local dev, reset link is displayed on screen.

### 🔐 **Two-Factor Authentication (2FA)**

**How to enable**:
1. Log in
2. Go to Settings → Security tab
3. Click "Enable 2FA"
4. Scan QR code with Google Authenticator / Authy
5. Done! You'll need the 6-digit code on future logins

**Recommended**: Enable 2FA for admin account!

### 🍎 **OAuth Support** (Coming Soon)

Planned support for:
- Sign in with Apple
- Sign in with Google
- Sign in with GitHub

**Status**: Framework ready, needs OAuth credentials

---

## 🏗️ Database Schema

### Users Table
```sql
- id: Primary key
- email: Unique email address
- username: Unique username
- hashed_password: Bcrypt hashed
- full_name: Display name
- role: 'admin' or 'user'
- is_active: Account status
- two_factor_enabled: 2FA status
- created_at: Registration date
```

### User Settings Table
```sql
- user_id: Foreign key to users
- bankroll: Current bankroll
- risk_profile: 'small', 'medium', 'large'
- min_edge: Minimum edge filter
- min_probability: Min win probability
- notifications_enabled: Push notifications
```

### Tracked Bets Table
```sql
- id: Bet ID
- user_id: Foreign key
- game_description: Game info
- bet_type: What was bet
- bet_size: Amount wagered
- odds: Betting odds
- status: 'pending', 'won', 'lost'
- result: Profit/loss amount
```

---

## 🔒 Security Features

### Password Security
- ✅ Bcrypt hashing (industry standard)
- ✅ Minimum 8 characters
- ✅ Salted hashes (rainbow table resistant)
- ✅ Password reset tokens expire after 1 hour

### Session Security
- ✅ Streamlit session state (server-side)
- ✅ No tokens in URLs (except password reset)
- ✅ Auto-logout on browser close

### Database Security
- ✅ SQLite with proper permissions
- ✅ No raw SQL (parameterized queries)
- ✅ Input validation
- ✅ XSS prevention (Streamlit handles this)

### Admin Protection
- ✅ Only b_flink@hotmail.com gets admin role
- ✅ Admin features hidden from regular users
- ✅ Role checked on every page load

---

## 📱 Usage Examples

### Example 1: Regular User (Daily Betting)

**Monday Morning**:
1. Open app → http://localhost:8501
2. Sign in with your account
3. Go to "My Picks"
4. See 3 recommended bets
5. Tap "Track Bet" on each
6. Place bets at your sportsbook

**Monday Evening**:
1. Open app
2. Go to "Performance"
3. Update bet statuses (won/lost)
4. See updated profit and win rate

**Weekly**:
1. Go to "Bankroll"
2. Update bankroll with new total
3. Review risk profile

---

### Example 2: Admin User (System Management)

**Weekly Maintenance**:
1. Sign in as admin
2. Go to "Admin Panel"
3. Click "🎓 Model Training"
4. Click "🎯 Quick Train"
5. Wait 5 minutes
6. View improved model stats

**Monthly Optimization**:
1. Go to "🤖 Bulldog AI"
2. Click "🔍 Discover New Edges"
3. Review discovered strategies
4. Deploy winning strategies

---

## 🆘 Troubleshooting

### Can't Login?

**Check**:
- Username/email is correct
- Password is correct (case-sensitive)
- Account is active
- Database exists (`data/auth.db`)

**Reset password**:
1. Use "Reset Password" tab
2. Enter your email
3. Follow reset link

---

### 2FA Not Working?

**Check**:
- Code is current (refreshes every 30 seconds)
- Time on your device is correct
- Using correct authenticator app

**Disable 2FA**:
- Contact admin (b_flink@hotmail.com)
- Admin can disable 2FA in database

---

### Admin Panel Not Showing?

**Check**:
- You're logged in as b_flink@hotmail.com
- Look for "🔧 Admin Panel" in sidebar
- Clear browser cache and reload

---

## 🔧 Configuration

### Change Admin Credentials

**Edit**: `dashboard/auth_system.py`

```python
ADMIN_EMAIL = "your_email@domain.com"
ADMIN_USERNAME = "your_username"
ADMIN_PASSWORD = "your_password"
```

Then delete `data/auth.db` and restart app.

---

### Add OAuth Providers

**Edit**: `config/auth_keys.env`

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret

# Apple Sign In
APPLE_CLIENT_ID=your_apple_id
APPLE_TEAM_ID=your_team_id

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_id
GITHUB_CLIENT_SECRET=your_github_secret
```

---

### Enable Email (Password Reset)

**Edit**: `dashboard/auth_system.py`

Find `send_reset_email()` function and update SMTP settings:

```python
def send_reset_email(email, token):
    # Configure SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"
    
    # Send email
    # ... (code provided in function)
```

---

## 📊 User Management (Admin)

### View All Users (SQL Query)

```sql
SELECT email, username, role, created_at, last_login
FROM users
WHERE is_active = 1
ORDER BY created_at DESC;
```

### Make User Admin (SQL)

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'user@email.com';
```

### Disable User (SQL)

```sql
UPDATE users
SET is_active = 0
WHERE email = 'user@email.com';
```

---

## 🚀 Deployment

### Streamlit Cloud

1. **Push to GitHub**
2. **Go to**: https://streamlit.io/cloud
3. **Settings**:
   - Main file: `dashboard/app_complete.py`
   - Python version: 3.10+
4. **Secrets**: Add `config/auth_keys.env` as secrets
5. **Deploy!**

### Heroku

```bash
# Create Procfile
echo "web: streamlit run dashboard/app_complete.py" > Procfile

# Deploy
heroku create nfl-edge-finder
git push heroku main
```

---

## 📞 Support

**Admin Contact**: b_flink@hotmail.com

**Issues**: Report security issues privately to admin

**Feature Requests**: Open GitHub issue

---

## 🎉 Summary

You now have:
- ✅ **Secure authentication** (bcrypt, 2FA, password reset)
- ✅ **Admin access** for b_flink@hotmail.com only
- ✅ **Nice features** for all users (simple, logical, useful)
- ✅ **Advanced controls** for admin (Bulldog, training, automation)
- ✅ **One-command setup** (everything installs automatically)

**Start the app**: `streamlit run dashboard/app_complete.py`

**Enjoy!** 🏈💰

