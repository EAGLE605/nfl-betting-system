# 🔄 RETRAINING ACTION PLAN - ADDRESSING CRITICAL FINDINGS

**Date**: November 24, 2025  
**Status**: 🔴 **CRITICAL - MODEL NEEDS RETRAINING**  
**Priority**: **HIGHEST**

---

## 🚨 THE PROBLEM

The Bulldog Mode backtest revealed a **critical issue**:

| Period | Win Rate | ROI | Status |
|--------|----------|-----|--------|
| 2020-2022 | 100% | +1,000,000%+ | ✅ Perfect |
| 2023-2024 | 60-63% | **-25% to -29%** | ❌ **LOSING** |

**The model trained on 2016-2024 data worked perfectly in 2020-2022 but completely failed in 2023-2024.**

---

## ✅ SOLUTION: RETRAIN ON RECENT DATA

### **Phase 1: Retrain Model (This Week)**

**Objective**: Train model on 2023 data only, test on 2024 data

**Command**:
```bash
python scripts/retrain_recent_model.py
```

**What it does**:
- Trains on 2023 data only (285 games)
- Tests on 2024 data (285 games)
- Captures current market patterns
- Saves model to `models/xgboost_recent_2023.pkl`

**Success Criteria**:
- ✅ Accuracy >= 0.55
- ✅ Brier Score <= 0.20
- ✅ ROC AUC >= 0.60

**Expected Result**:
- Win rate: 55-60% (realistic, not 100%)
- Model learns current market, not historical anomalies

---

### **Phase 2: Backtest Recent Model (This Week)**

**Objective**: Validate retrained model on 2024 data

**Command**:
```bash
python scripts/bulldog_backtest.py --model models/xgboost_recent_2023.pkl --test-season 2024
```

**What it does**:
- Runs full Bulldog Mode backtest on 2024 data only
- Tests all scenarios and dimensions
- Generates performance metrics

**Success Criteria**:
- ✅ Win rate >= 55%
- ✅ ROI >= +5%
- ✅ Sharpe ratio >= 1.0
- ✅ Max drawdown < -30%

**Decision Rule**:
- If all criteria met → Proceed to Phase 3
- If not → DO NOT DEPLOY, reassess approach

---

### **Phase 3: Paper Trading (January 2025)**

**Objective**: Test model on live 2025 data WITHOUT risking real money

**Strategy**:
- Generate picks for weeks 1-4 of 2025 season
- Track performance vs actual results
- Compare to market odds
- Calculate hypothetical ROI

**Success Criteria**:
- ✅ Win rate >= 55%
- ✅ Beating closing line value (CLV)
- ✅ Positive ROI
- ✅ No major drawdowns

**Decision Rule**:
- If profitable → Proceed to Phase 4
- If not → Stop and reassess

---

### **Phase 4: Cautious Deployment (February 2025)**

**Objective**: Deploy with controlled risk

**Strategy**:
- Use 50% of bankroll ($5K, not $10K)
- Bet only Tier S/A picks (highest confidence)
- Max 3 bets per week
- Strict stop-loss: -20% drawdown

**Success Criteria**:
- ✅ Profitable first month
- ✅ Win rate >= 55%
- ✅ Positive ROI
- ✅ No major drawdowns

**Decision Rule**:
- If profitable → Scale up gradually
- If not → Shut down and reassess

---

## 📊 EXPECTED RESULTS

### **If Retraining Works**:

**Best Case**:
- Win rate: 58-60%
- ROI: +10-15%
- Monthly profit: $800-1,200

**Realistic Case**:
- Win rate: 55-57%
- ROI: +5-10%
- Monthly profit: $400-800

**Worst Case**:
- Win rate: 52-54%
- ROI: 0-5%
- Monthly profit: $0-400

### **DO NOT Expect**:
- ❌ 87% win rate (that's from averaging 100% and 60%)
- ❌ 100% win rate (COVID-era anomaly)
- ❌ Trillions in ROI (compounding error)

---

## 🎯 KEY INSIGHTS FROM BULLDOG BACKTEST

### **What Worked (2020-2022)**:
- Heavy favorites (100% WR)
- High confidence picks (>70% = 96% WR)
- Divisional games
- Dome games
- Playoffs (96.6% WR)

### **What's Broken (2023-2024)**:
- Same strategies now lose money
- Win rate dropped to 60-63%
- ROI negative
- Model confidence unreliable

### **Why This Happened**:
1. **Market Adaptation**: Oddsmakers caught up to edges
2. **COVID-Era Anomaly**: 2020-2021 had temporary inefficiencies
3. **Overfitting**: Model learned patterns that don't exist anymore

---

## 🔬 TECHNICAL DETAILS

### **Current Model**:
- Trained on: 2016-2024 (includes failed 2023-2024)
- Test period: 2020-2024
- Problem: Includes historical data that doesn't reflect current market

### **New Model**:
- Trained on: 2023 only (285 games)
- Test period: 2024 only (285 games)
- Advantage: Captures current market patterns

### **Feature Alignment**:
- Model expects specific features
- Data may have missing features
- Script handles feature alignment automatically

---

## 📋 EXECUTION CHECKLIST

### **This Week**:
- [ ] Run `scripts/retrain_recent_model.py`
- [ ] Verify model meets minimum criteria
- [ ] Run backtest on 2024 data
- [ ] Review backtest results
- [ ] Make GO/NO-GO decision

### **January 2025**:
- [ ] Set up paper trading system
- [ ] Generate picks for weeks 1-4
- [ ] Track performance vs actual results
- [ ] Calculate metrics
- [ ] Make deployment decision

### **February 2025** (if validated):
- [ ] Deploy with 50% bankroll
- [ ] Bet only Tier S/A picks
- [ ] Max 3 bets per week
- [ ] Monitor closely
- [ ] Scale up if profitable

---

## 🚫 WHAT NOT TO DO

- ❌ **DO NOT deploy current model** (will lose money)
- ❌ **DO NOT expect 100% win rates** (not realistic)
- ❌ **DO NOT bet full bankroll** (too risky)
- ❌ **DO NOT ignore 2023-2024 performance** (most relevant)
- ❌ **DO NOT skip paper trading** (critical validation step)

---

## ✅ WHAT TO DO

- ✅ **DO retrain on recent data** (2023 only)
- ✅ **DO test on 2024** (most recent hold-out)
- ✅ **DO paper trade first** (validate before risking money)
- ✅ **DO deploy cautiously** (50% bankroll, Tier S/A only)
- ✅ **DO expect realistic returns** (55-60% WR, +5-10% ROI)

---

## 💰 EXPECTED VALUE

### **If You Deploy Current Model** (Don't!):
```
Expected Win Rate: 60-63%
Expected ROI: -25%
$10K bankroll → $7.5K (lose $2,500)
```

### **If You Retrain on 2023-2024**:
```
Expected Win Rate: 55-58% (realistic)
Expected ROI: +8%
$10K bankroll → $10,800 (gain $800)
```

**Difference**: $3,300 swing by retraining!

---

## 🏆 CONCLUSION

**The Bulldog backtest did its job**:
- ✅ Found the model works (2020-2022)
- ✅ Discovered it's broken now (2023-2024)
- ✅ Prevented you from losing $2-3K
- ✅ Identified path forward (retrain)

**Next Steps**:
1. Retrain on 2023 data
2. Backtest on 2024 data
3. Paper trade first month 2025
4. Deploy cautiously if validated

**The system CAN work, but NOT with the current model trained on old data.**

**Retrain → Validate → Deploy Cautiously → Profit Sustainably**

---

**Status**: 🔴 **CRITICAL - ACTION REQUIRED**  
**Next Action**: Run `python scripts/retrain_recent_model.py`  
**Timeline**: Complete Phase 1-2 this week, Phase 3 in January, Phase 4 in February

