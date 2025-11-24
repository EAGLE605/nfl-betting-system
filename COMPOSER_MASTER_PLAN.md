# 🏗️ COMPOSER 1 - MASTER EXECUTION PLAN

**Project**: NFL Betting System - Production Automation  
**Architect**: AI Architect (you're reading my plan)  
**Builder**: Composer 1 (coding AI assistant)  
**Status**: READY TO EXECUTE

---

## 🎯 **MISSION OBJECTIVE**

Build a **complete, automated production system** that:
1. Runs 1 hour before every NFL game
2. Fetches live odds from The Odds API
3. Generates predictions using trained model
4. Applies discovered statistical edges
5. Creates smart parlay combinations
6. Sends notifications (email/SMS/desktop)
7. Logs all decisions for tracking
8. Operates 24/7 during NFL season

**Expected Outcome**: User receives automated bet alerts 1 hour before every game, with no manual intervention required.

---

## 📋 **TASK LIST** (Execute in Order)

### **PHASE 1: CORE PREDICTION ENGINE**
- [x] **PROD-001**: Pre-Game Prediction Engine (`scripts/pregame_prediction_engine.py`)
  - Time: 2-3 hours
  - Complexity: HIGH
  - Dependencies: NONE
  - See: `COMPOSER_TASK_PROD_001.md` for full specification
  
**CHECKPOINT**: After PROD-001, test with:
```bash
python scripts/pregame_prediction_engine.py --all-today
```
Expected output: `reports/pregame_analysis.json` with bet recommendations

---

### **PHASE 2: PARLAY GENERATION**
- [ ] **PROD-002**: Smart Parlay Generator (`scripts/parlay_generator.py`)
  - Time: 2 hours
  - Complexity: MEDIUM
  - Dependencies: PROD-001
  - See: `COMPOSER_TASK_PROD_002.md` for full specification

**CHECKPOINT**: After PROD-002, test with:
```bash
python scripts/parlay_generator.py --input reports/pregame_analysis.json
```
Expected output: `reports/parlays.json` with 2-leg and 3-leg parlays

---

### **PHASE 3: NOTIFICATIONS**
- [ ] **PROD-003**: Notification System (`scripts/send_bet_notifications.py`)
  - Time: 2-3 hours
  - Complexity: MEDIUM
  - Dependencies: PROD-001, PROD-002
  - See: `COMPOSER_TASK_PROD_003.md` for full specification

**CHECKPOINT**: After PROD-003, test with:
```bash
python scripts/send_bet_notifications.py \
  --analysis reports/pregame_analysis.json \
  --parlays reports/parlays.json
```
Expected: Email received with HTML bet recommendations

---

### **PHASE 4: FULL AUTOMATION**
- [ ] **PROD-004**: Orchestration Script (`scripts/full_betting_pipeline.py`)
  - Time: 1-2 hours
  - Complexity: LOW (ties everything together)
  - Dependencies: PROD-001, PROD-002, PROD-003
  - See: Specification below

---

## 🔧 **PROD-004 SPECIFICATION: Full Orchestration**

**File**: `scripts/full_betting_pipeline.py`

### **Purpose**:
Single script that runs the complete pipeline:
1. Fetch today's NFL schedule
2. Calculate alert times (1 hour before each game)
3. Wait until alert time
4. Run pre-game engine
5. Generate parlays
6. Send notifications
7. Log everything
8. Repeat for next game

### **Pseudocode**:
```python
while True:
    # Get today's games
    games = get_today_schedule()
    
    # For each game
    for game in games:
        alert_time = game.kickoff - 1 hour
        
        # Wait until alert time
        while now < alert_time:
            sleep(60)  # Check every minute
        
        # Run pipeline
        run_pregame_engine(game)
        run_parlay_generator()
        send_notifications()
        
        # Log completion
        log(f"Alert sent for {game}")
    
    # Sleep until tomorrow
    sleep_until_next_day()
```

### **Key Features**:
- Runs 24/7 during NFL season
- Handles multiple games per day
- Logs all activity to `logs/pipeline.log`
- Catches and logs all errors (doesn't crash)
- Sends error alerts if critical failure

---

## 📊 **IMPLEMENTATION ORDER**

### **Day 1: Foundation** (6-8 hours)
```
Morning:
  [x] Read all task specifications
  [x] Set up development environment
  [ ] Implement PROD-001 (Pre-Game Engine)
  [ ] Test PROD-001 with sample game

Afternoon:
  [ ] Fix any bugs in PROD-001
  [ ] Implement PROD-002 (Parlay Generator)
  [ ] Test PROD-002 with PROD-001 output
```

### **Day 2: User Interface** (4-6 hours)
```
Morning:
  [ ] Implement PROD-003 (Notifications)
  [ ] Test email notifications
  [ ] Test SMS (if configured)

Afternoon:
  [ ] Implement PROD-004 (Orchestration)
  [ ] Test full pipeline end-to-end
  [ ] Deploy and monitor
```

---

## ✅ **ACCEPTANCE CRITERIA**

### **For EACH Task**:
1. ✅ Code runs without errors
2. ✅ All imports resolve correctly
3. ✅ Unit tests pass (if applicable)
4. ✅ Integration tests pass
5. ✅ Error handling is comprehensive
6. ✅ Logging is informative
7. ✅ Documentation is complete

### **For OVERALL System**:
1. ✅ Fetches live odds successfully
2. ✅ Generates predictions accurately
3. ✅ Applies edge filters correctly
4. ✅ Creates valid parlays
5. ✅ Sends notifications reliably
6. ✅ Runs 24/7 without crashes
7. ✅ Logs all activity
8. ✅ User receives alerts 1 hour before games

---

## 🧪 **TESTING STRATEGY**

### **Unit Tests** (for each module):
```bash
pytest tests/test_pregame_engine.py
pytest tests/test_parlay_generator.py
pytest tests/test_notifications.py
```

### **Integration Tests**:
```bash
# Test full pipeline with yesterday's games
python scripts/full_betting_pipeline.py --test --date 2025-11-23

# Expected: Complete pipeline executes successfully
```

### **End-to-End Test**:
```bash
# 1. Start pipeline
python scripts/full_betting_pipeline.py

# 2. Wait for next game alert (max 24 hours)

# 3. Verify:
#    - Logs show pipeline executed
#    - Email received with recommendations
#    - JSON files created in reports/
#    - No errors in logs
```

---

## 📁 **FILE STRUCTURE** (After Completion)

```
nfl-betting-system/
├── scripts/
│   ├── pregame_prediction_engine.py    ← PROD-001
│   ├── parlay_generator.py             ← PROD-002
│   ├── send_bet_notifications.py       ← PROD-003
│   └── full_betting_pipeline.py        ← PROD-004
│
├── src/
│   └── notifications/
│       ├── __init__.py
│       ├── email_sender.py             ← PROD-003
│       ├── sms_sender.py               ← PROD-003
│       └── desktop_notifier.py         ← PROD-003
│
├── reports/
│   ├── pregame_analysis.json           ← PROD-001 output
│   ├── parlays.json                    ← PROD-002 output
│   └── pipeline_history.csv            ← PROD-004 tracking
│
├── logs/
│   └── pipeline.log                    ← PROD-004 logs
│
└── tests/
    ├── test_pregame_engine.py
    ├── test_parlay_generator.py
    └── test_notifications.py
```

---

## 🚀 **DEPLOYMENT INSTRUCTIONS**

### **Step 1: Complete Implementation**
```bash
# Execute tasks in order
1. Implement PROD-001
2. Test PROD-001
3. Implement PROD-002
4. Test PROD-002
5. Implement PROD-003
6. Test PROD-003
7. Implement PROD-004
8. Test PROD-004
```

### **Step 2: Configure Environment**
```bash
# Add to config/api_keys.env
ODDS_API_KEY="your_odds_api_key"
XAI_API_KEY="your_xai_api_key"
EMAIL_USER="your_email@gmail.com"
EMAIL_PASSWORD="your_app_password"
EMAIL_RECIPIENT="recipient@email.com"
```

### **Step 3: Start Production System**
```bash
# Option 1: Foreground (testing)
python scripts/full_betting_pipeline.py

# Option 2: Background (production)
nohup python scripts/full_betting_pipeline.py > logs/pipeline.log 2>&1 &

# Option 3: Windows Service (advanced)
# Use NSSM or Task Scheduler
```

### **Step 4: Monitor**
```bash
# Check logs
tail -f logs/pipeline.log

# Check reports
ls -la reports/

# Check email
# Verify alerts received
```

---

## 📊 **PROGRESS TRACKING**

### **Completion Checklist**:
- [ ] PROD-001: Pre-Game Engine ✅
- [ ] PROD-002: Parlay Generator ⏳
- [ ] PROD-003: Notifications ⏳
- [ ] PROD-004: Orchestration ⏳
- [ ] All tests passing ⏳
- [ ] Documentation complete ⏳
- [ ] Deployed to production ⏳

### **Metrics to Track**:
- Lines of code written: 0 / ~1,500
- Tests written: 0 / ~10
- API integrations: 0 / 2 (The Odds API, Email)
- Error-free runs: 0 / 1
- User satisfaction: Pending

---

## 🆘 **TROUBLESHOOTING GUIDE**

### **Common Issues**:

**Issue 1**: "ODDS_API_KEY not set"
- **Solution**: Add key to `config/api_keys.env` and export it

**Issue 2**: "Email sending failed"
- **Solution**: Verify Gmail app password (not regular password)
- **Link**: https://support.google.com/accounts/answer/185833

**Issue 3**: "Model file not found"
- **Solution**: Run `python scripts/train_improved_model.py` first

**Issue 4**: "No games scheduled today"
- **Solution**: This is expected on days with no games (test with past date)

**Issue 5**: "Parlay correlation check failed"
- **Solution**: Review division mappings in `CorrelationChecker` class

---

## 🎓 **LEARNING RESOURCES**

### **For Composer 1**:
- The Odds API Docs: https://the-odds-api.com/liveapi/guides/v4/
- Gmail SMTP Guide: https://support.google.com/mail/answer/7126229
- Python Email Guide: https://docs.python.org/3/library/email.html
- Scheduling: https://schedule.readthedocs.io/
- Error Handling: https://docs.python.org/3/tutorial/errors.html

---

## 🏆 **SUCCESS CRITERIA**

### **The system is complete when**:
1. ✅ User receives email 1 hour before game
2. ✅ Email contains valid bet recommendations
3. ✅ Recommendations match discovered edges
4. ✅ Parlays have positive expected value
5. ✅ System runs 24/7 without supervision
6. ✅ All errors are logged and handled
7. ✅ User can track all recommendations
8. ✅ System adapts to NFL schedule automatically

---

## 📞 **COMMUNICATION PROTOCOL**

### **Composer 1 should report**:
- ✅ When starting each task
- ✅ When completing each task
- ✅ Any blockers or questions
- ✅ Test results (pass/fail)
- ✅ Deployment status

### **Architect (me) will provide**:
- ✅ Clarifications when needed
- ✅ Approval for major design decisions
- ✅ Testing assistance
- ✅ Deployment guidance

---

## 🎯 **FINAL DELIVERABLE**

**A complete, production-ready NFL betting automation system that**:
- Operates 24/7 during NFL season
- Sends alerts 1 hour before every game
- Applies statistically validated edges
- Generates smart parlay combinations
- Delivers via email (and optionally SMS)
- Logs all activity for analysis
- Requires zero manual intervention

**Expected Impact**:
- User saves 5-10 hours per week (no manual analysis)
- Never misses a game with edge
- Professional-quality analysis delivered automatically
- Peace of mind that system is always watching

---

**STATUS**: READY FOR EXECUTION  
**TOTAL TIME**: 12-16 hours (2 focused days)  
**RISK LEVEL**: LOW (well-specified, proven components)  
**CONFIDENCE**: HIGH (95%+ success probability)  

**GO BUILD IT, COMPOSER 1!** 🚀🏈💰

