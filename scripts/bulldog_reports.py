"""BULLDOG MODE: Report Generation

Generate all required markdown reports from backtest results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("reports/bulldog_mode")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def df_to_markdown(df: pd.DataFrame, index: bool = False) -> str:
    """Convert DataFrame to markdown table."""
    if len(df) == 0:
        return ""

    # Format numeric columns
    df_formatted = df.copy()
    for col in df_formatted.columns:
        if df_formatted[col].dtype in ["float64", "float32"]:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else ""
            )
        elif df_formatted[col].dtype in ["int64", "int32"]:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{int(x)}" if pd.notna(x) else ""
            )

    # Create markdown table
    lines = []

    # Header
    headers = list(df_formatted.columns)
    if index:
        headers = [""] + headers
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Rows
    for idx, row in df_formatted.iterrows():
        values = [str(v) for v in row.values]
        if index:
            values = [str(idx)] + values
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines) + "\n"


class BulldogReports:
    """Generate all Bulldog Mode reports."""

    def __init__(self):
        """Initialize report generator."""
        # Load data
        self.results_df = pd.read_csv(
            OUTPUT_DIR / "data" / "bulldog_performance_by_segment.csv"
        )
        self.bets_df = pd.read_csv(OUTPUT_DIR / "data" / "bulldog_backtest_results.csv")

        # Load analysis results
        analysis_path = OUTPUT_DIR / "data" / "bulldog_analysis_results.json"
        if analysis_path.exists():
            with open(analysis_path, "r") as f:
                self.analysis = json.load(f)
        else:
            self.analysis = {}

        # Load feature importance
        feature_path = OUTPUT_DIR / "data" / "bulldog_feature_importance.csv"
        if feature_path.exists():
            self.feature_importance = pd.read_csv(feature_path)
        else:
            self.feature_importance = pd.DataFrame()

    def generate_executive_summary(self) -> str:
        """Generate executive summary report."""
        logger.info("Generating executive summary...")

        # Get main results (full period)
        main_result = (
            self.results_df[self.results_df["name"] == "Full Period (2020-2024)"].iloc[
                0
            ]
            if len(self.results_df) > 0
            else None
        )

        if main_result is None:
            main_result = self.results_df.iloc[0] if len(self.results_df) > 0 else None

        report = f"""# 🐕 BULLDOG MODE BACKTEST - EXECUTIVE SUMMARY

**Date**: {datetime.now().strftime('%B %d, %Y')}  
**Mode**: 🔥 BULLDOG MODE - NO COMPROMISES  
**Period**: 2020-2024  
**Model**: xgboost_improved.pkl

---

## 📊 KEY METRICS

"""

        if main_result is not None:
            report += f"""| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Win Rate | {main_result['win_rate']:.2f}% | >60% | {'✅' if main_result['win_rate'] > 60 else '❌'} |
| ROI | {main_result['roi']:.2f}% | >10% | {'✅' if main_result['roi'] > 10 else '❌'} |
| Total Profit | ${main_result['total_profit']:,.2f} | >$5K | {'✅' if main_result['total_profit'] > 5000 else '❌'} |
| Sharpe Ratio | {main_result['sharpe_ratio']:.2f} | >1.5 | {'✅' if main_result['sharpe_ratio'] > 1.5 else '❌'} |
| Max Drawdown | {main_result['max_drawdown']:.2f}% | <-25% | {'✅' if main_result['max_drawdown'] > -25 else '❌'} |
| Total Bets | {int(main_result['total_bets']):,} | >2,000 | {'✅' if main_result['total_bets'] > 2000 else '❌'} |
| Avg CLV | {main_result['avg_clv']:.2f}% | >0% | {'✅' if main_result['avg_clv'] > 0 else '❌'} |

"""

        # Top 3 findings
        report += """## 🎯 TOP 3 FINDINGS

1. **Finding 1**: [To be filled from analysis]
2. **Finding 2**: [To be filled from analysis]
3. **Finding 3**: [To be filled from analysis]

---

## 💡 TOP 3 RECOMMENDATIONS

1. **Recommendation 1**: [To be filled from analysis]
2. **Recommendation 2**: [To be filled from analysis]
3. **Recommendation 3**: [To be filled from analysis]

---

## ✅ GO/NO-GO DECISION

[Decision will be based on comprehensive analysis]

**Status**: PENDING FULL ANALYSIS

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_full_report(self) -> str:
        """Generate full backtest report."""
        logger.info("Generating full report...")

        report = f"""# 🐕 BULLDOG MODE BACKTEST - FULL REPORT

**Date**: {datetime.now().strftime('%B %d, %Y')}  
**Mode**: 🔥 BULLDOG MODE - NO COMPROMISES  
**Period**: 2020-2024  
**Model**: xgboost_improved.pkl

---

## A. EXECUTIVE SUMMARY

[See separate executive summary document]

---

## B. PERFORMANCE METRICS

### Overall Performance

"""

        # Main metrics table
        main_result = (
            self.results_df[self.results_df["name"] == "Full Period (2020-2024)"].iloc[
                0
            ]
            if len(self.results_df) > 0
            else None
        )

        if main_result is not None:
            report += f"""
| Metric | Result |
|--------|--------|
| Total Bets | {int(main_result['total_bets']):,} |
| Wins | {int(main_result['wins']):,} |
| Losses | {int(main_result['losses']):,} |
| Win Rate | {main_result['win_rate']:.2f}% |
| Total Profit | ${main_result['total_profit']:,.2f} |
| ROI | {main_result['roi']:.2f}% |
| Sharpe Ratio | {main_result['sharpe_ratio']:.2f} |
| Max Drawdown | {main_result['max_drawdown']:.2f}% |
| Avg Bet Size | ${self.bets_df['bet_size'].mean():.2f} |
| Largest Win | ${self.bets_df[self.bets_df['result']=='win']['profit'].max():.2f} |
| Largest Loss | ${self.bets_df[self.bets_df['result']=='loss']['profit'].min():.2f} |
| Avg CLV | {main_result['avg_clv']:.2f}% |
| Positive CLV | {main_result['positive_clv_pct']:.1f}% |

"""

        # By-segment performance
        report += """## C. BY-SEGMENT PERFORMANCE

### Time Period Breakdown

"""

        time_periods = self.results_df[
            self.results_df["name"].str.contains(
                "Season|Period|Early|Late|Regular|Playoff", na=False
            )
        ]

        if len(time_periods) > 0:
            report += df_to_markdown(
                time_periods[["name", "total_bets", "win_rate", "roi", "sharpe_ratio"]]
            )
            report += "\n\n"

        # Game characteristics
        report += """### Game Characteristics Breakdown

"""

        game_chars = self.results_df[
            self.results_df["name"].str.contains(
                "Favorite|Underdog|Scoring|Divisional|Weather|Dome", na=False
            )
        ]

        if len(game_chars) > 0:
            report += df_to_markdown(
                game_chars[["name", "total_bets", "win_rate", "roi", "sharpe_ratio"]]
            )
            report += "\n\n"

        # Edge discovery
        report += """## D. EDGE DISCOVERY

### Discovered Edges

"""

        # Find profitable edges
        profitable = self.results_df[
            (self.results_df["roi"] > 5) & (self.results_df["total_bets"] > 20)
        ].sort_values("roi", ascending=False)

        if len(profitable) > 0:
            for idx, edge in profitable.head(10).iterrows():
                report += f"""
**EDGE #{idx+1}: {edge['name']}**
- Win Rate: {edge['win_rate']:.2f}%
- ROI: {edge['roi']:.2f}%
- Sample Size: {int(edge['total_bets'])} bets
- Sharpe Ratio: {edge['sharpe_ratio']:.2f}

"""

        # Risk analysis
        report += """## E. RISK ANALYSIS

### Drawdown Analysis

"""

        if "drawdown" in self.analysis:
            dd = self.analysis["drawdown"]
            report += f"""
- Max Drawdown: {dd.get('max_drawdown', 0):.2f}%
- Number of Drawdown Periods: {dd.get('num_drawdown_periods', 0)}
- Average Drawdown Duration: {dd.get('avg_drawdown_duration', 0):.1f} bets
- Worst Drawdown: {dd.get('worst_drawdown', 0):.2f}%

"""

        report += f"""

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_feature_analysis(self) -> str:
        """Generate feature analysis report."""
        logger.info("Generating feature analysis report...")

        report = f"""# 🐕 BULLDOG MODE - FEATURE ANALYSIS REPORT

**Date**: {datetime.now().strftime('%B %d, %Y')}

---

## A. FEATURE IMPORTANCE RANKING

### Top 20 Features

"""

        if len(self.feature_importance) > 0:
            top_20 = self.feature_importance.head(20)
            report += df_to_markdown(
                top_20[["feature", "importance_pct", "cumulative_pct"]]
            )
            report += "\n\n"

        report += """## B. FEATURE INTERACTIONS

[Feature interaction analysis to be added]

---

## C. FEATURE ENGINEERING RECOMMENDATIONS

### Recommended New Features

1. [To be determined from analysis]

### Features to Remove

1. [To be determined from analysis]

### Features to Modify

1. [To be determined from analysis]

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_optimization_report(self) -> str:
        """Generate optimization report."""
        logger.info("Generating optimization report...")

        report = f"""# 🐕 BULLDOG MODE - OPTIMIZATION REPORT

**Date**: {datetime.now().strftime('%B %d, %Y')}

---

## A. OPTIMAL BET SIZING

### Kelly Fraction Comparison

"""

        kelly_results = self.results_df[
            self.results_df["name"].str.contains("Kelly", na=False)
        ]

        if len(kelly_results) > 0:
            report += df_to_markdown(
                kelly_results[
                    [
                        "name",
                        "total_bets",
                        "win_rate",
                        "roi",
                        "sharpe_ratio",
                        "max_drawdown",
                    ]
                ]
            )
            report += "\n\n"

        report += """### Recommended Bet Sizing

[Recommendation based on analysis]

---

## B. OPTIMAL CONFIDENCE THRESHOLD

### Confidence Level Comparison

"""

        conf_results = self.results_df[
            self.results_df["name"].str.contains("Confidence", na=False)
        ]

        if len(conf_results) > 0:
            report += df_to_markdown(
                conf_results[["name", "total_bets", "win_rate", "roi", "sharpe_ratio"]]
            )
            report += "\n\n"

        report += """### Recommended Confidence Threshold

[Recommendation based on analysis]

---

## C. OPTIMAL TIER SYSTEM

[Current tier performance and recommendations]

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_edge_playbook(self) -> str:
        """Generate edge playbook."""
        logger.info("Generating edge playbook...")

        report = f"""# 🐕 BULLDOG MODE - EDGE PLAYBOOK

**Date**: {datetime.now().strftime('%B %d, %Y')}

---

## DISCOVERED EDGES

"""

        # Find all profitable edges
        profitable = self.results_df[
            (self.results_df["roi"] > 0) & (self.results_df["total_bets"] > 10)
        ].sort_values("roi", ascending=False)

        for idx, edge in profitable.iterrows():
            report += f"""
### EDGE #{idx+1}: {edge['name']}

**Description**: [To be filled]  
**Historical Performance**: {edge['win_rate']:.1f}% win rate, {edge['roi']:.1f}% ROI  
**Sample Size**: {int(edge['total_bets'])} bets  
**Statistical Significance**: [To be calculated]  
**When to Use**: [To be determined]  
**When NOT to Use**: [To be determined]  
**Bet Sizing**: [To be determined]  
**Expected Value**: [To be calculated]

---

"""

        report += f"""

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_statistical_validation(self) -> str:
        """Generate statistical validation report."""
        logger.info("Generating statistical validation report...")

        report = f"""# 🐕 BULLDOG MODE - STATISTICAL VALIDATION REPORT

**Date**: {datetime.now().strftime('%B %d, %Y')}

---

## A. HYPOTHESIS TESTING

### Win Rate Significance Test

"""

        if "statistical_significance" in self.analysis:
            ss = self.analysis["statistical_significance"]
            report += f"""
- **H0**: Win rate = 50% (random)
- **H1**: Win rate > 50% (skill)
- **Observed Win Rate**: {ss.get('win_rate', 0):.2f}%
- **Z-Score**: {ss.get('z_score', 0):.2f}
- **P-Value**: {ss.get('p_value', 1):.6f}
- **Significant at 95%**: {'Yes' if ss.get('significant_95', False) else 'No'}
- **Significant at 99%**: {'Yes' if ss.get('significant_99', False) else 'No'}
- **95% Confidence Interval**: [{ss.get('ci_95_lower', 0):.2f}%, {ss.get('ci_95_upper', 100):.2f}%]

"""

        report += """## B. VARIANCE ANALYSIS

"""

        if "variance" in self.analysis:
            var = self.analysis["variance"]
            report += f"""
- **Actual Profit**: ${var.get('actual_profit', 0):,.2f}
- **Simulated Mean**: ${var.get('simulated_mean_profit', 0):,.2f}
- **Z-Score**: {var.get('z_score', 0):.2f}
- **P-Value**: {var.get('p_value', 1):.4f}
- **Probability of Positive**: {var.get('probability_positive', 0):.1%}

"""

        report += """## C. SHARPE RATIO ANALYSIS

[Sharpe ratio analysis to be added]

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_model_comparison(self) -> str:
        """Generate model comparison report."""
        logger.info("Generating model comparison report...")

        report = f"""# 🐕 BULLDOG MODE - MODEL COMPARISON REPORT

**Date**: {datetime.now().strftime('%B %d, %Y')}

---

## MODEL COMPARISON

[Model comparison to be added when multiple models are tested]

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def generate_all_reports(self):
        """Generate all reports."""
        logger.info("=" * 80)
        logger.info("GENERATING ALL BULLDOG MODE REPORTS")
        logger.info("=" * 80)

        reports = {
            "BULLDOG_BACKTEST_EXECUTIVE_SUMMARY.md": self.generate_executive_summary(),
            "BULLDOG_BACKTEST_FULL_REPORT.md": self.generate_full_report(),
            "BULLDOG_FEATURE_ANALYSIS.md": self.generate_feature_analysis(),
            "BULLDOG_OPTIMIZATION_REPORT.md": self.generate_optimization_report(),
            "BULLDOG_EDGE_PLAYBOOK.md": self.generate_edge_playbook(),
            "BULLDOG_STATISTICAL_VALIDATION.md": self.generate_statistical_validation(),
            "BULLDOG_MODEL_COMPARISON.md": self.generate_model_comparison(),
        }

        for filename, content in reports.items():
            filepath = OUTPUT_DIR / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"✓ Generated {filename}")

        logger.info("\n" + "=" * 80)
        logger.info("ALL REPORTS GENERATED")
        logger.info("=" * 80)
        logger.info(f"Reports saved to: {OUTPUT_DIR}")


def main():
    """Main execution."""
    reporter = BulldogReports()
    reporter.generate_all_reports()


if __name__ == "__main__":
    main()
