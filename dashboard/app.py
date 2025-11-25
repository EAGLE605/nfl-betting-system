"""
GAMELOCK AI - NFL Betting Dashboard

Real data. Real predictions. Real results.
"""

import os
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Local imports
from dashboard.data_loader import (
    calculate_season_record,
    format_picks_for_display,
    generate_predictions,
    get_current_week,
    get_espn_scoreboard,
    get_live_odds,
    get_model_info,
    get_weekly_performance,
    load_backtest_metrics,
    load_bet_history,
    load_daily_picks,
    run_backtest,
)

# AI Providers
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="GAMELOCK AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# SECRETS MANAGEMENT
# =============================================================================
def get_secret(key: str) -> str:
    """Get secret from Streamlit secrets or environment."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, "")


# API Keys
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
XAI_API_KEY = get_secret("XAI_API_KEY")
ODDS_API_KEY = get_secret("ODDS_API_KEY")

# Configure Gemini if available
if GENAI_AVAILABLE and GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception:
        pass


# =============================================================================
# AI FUNCTIONS
# =============================================================================
def generate_analysis(pick_data: dict, provider: str = "grok") -> tuple:
    """Generate AI analysis for a pick."""
    prompt = f"""You are a sharp sports betting analyst. Give a confident 2-3 sentence analysis:

Game: {pick_data.get('Game', 'Unknown')}
BET: {pick_data.get('Pick', '')} {pick_data.get('Line', '')} ({pick_data.get('Type', 'ML')})
Odds: {pick_data.get('Odds', '')}
Confidence: {pick_data.get('Confidence', 0)}%
EV: +{pick_data.get('EV', 0)}%

Explain WHY this bet wins. Be specific about matchups, trends, or edges."""

    # Try Grok first (xAI)
    if provider == "grok" and OPENAI_AVAILABLE and XAI_API_KEY:
        try:
            client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)
            response = client.chat.completions.create(
                model="grok-3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sharp sports betting analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content, "Grok-3"
        except Exception:
            pass

    # Try GPT
    if provider == "gpt" and OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return response.choices[0].message.content, "GPT-4o"
        except Exception:
            pass

    # Try Claude
    if provider == "claude" and ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text, "Claude"
        except Exception:
            pass

    # Try Gemini
    if provider == "gemini" and GENAI_AVAILABLE and GOOGLE_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text, "Gemini"
        except Exception:
            pass

    # Fallback
    return (
        f"Model shows {pick_data.get('Confidence', 0):.0f}% confidence on {pick_data.get('Pick', 'this pick')}.",
        "Fallback",
    )


# =============================================================================
# CSS STYLING
# =============================================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap');
    
    :root {
        --neon-green: #22c55e;
        --neon-blue: #3b82f6;
        --neon-purple: #8b5cf6;
        --dark-bg: #0a0f1a;
        --card-bg: #111827;
    }
    
    html, body, .stApp { 
        background: linear-gradient(135deg, #0a0f1a 0%, #0f172a 50%, #1a1a2e 100%);
        color: #e2e8f0; 
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding: 1rem 2rem; max-width: 100%; }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
        padding: 10px; 
        border-radius: 16px; 
        gap: 8px;
        border: 1px solid #374151;
    }
    
    .stTabs [data-baseweb="tab"] { 
        background: transparent;
        border-radius: 12px; 
        color: #9ca3af; 
        font-weight: 700; 
        padding: 14px 28px;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .stTabs [aria-selected="true"] { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; 
        color: white !important; 
    }
    
    [data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 16px; 
        padding: 24px;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #64748b !important;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }
    
    .stButton > button { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none; 
        color: white; 
        font-weight: 700;
        font-family: 'Orbitron', sans-serif;
        border-radius: 12px;
        padding: 12px 24px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .pulse { animation: pulse 2s infinite; }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# LOAD DATA
# =============================================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_metrics():
    return load_backtest_metrics()


@st.cache_data(ttl=300)
def get_cached_history():
    return load_bet_history()


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_cached_picks():
    return load_daily_picks()


# Load data
metrics = get_cached_metrics()
bet_history = get_cached_history()
daily_picks = get_cached_picks()
season_record = calculate_season_record(bet_history)
current_week = get_current_week()


# =============================================================================
# HEADER
# =============================================================================
col_title, col_status = st.columns([3, 1])

with col_title:
    # Build AI providers badge
    ai_list = []
    if OPENAI_AVAILABLE and XAI_API_KEY:
        ai_list.append("Grok")
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        ai_list.append("GPT")
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        ai_list.append("Claude")
    if GENAI_AVAILABLE and GOOGLE_API_KEY:
        ai_list.append("Gemini")

    ai_badge = f"""<span style='
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #fff; padding: 6px 14px; border-radius: 20px;
        font-size: 0.7rem; font-weight: 700; font-family: Orbitron;
        margin-left: 12px;
    '>{' • '.join(ai_list) if ai_list else 'NO AI'}</span>"""

    data_badge = (
        '<span style="background: #22c55e; color: #fff; padding: 4px 10px; border-radius: 12px; font-size: 0.65rem; font-weight: 600; font-family: Orbitron; margin-left: 8px;">REAL DATA</span>'
        if metrics.get("total_bets", 0) > 0
        else '<span style="background: #f59e0b; color: #000; padding: 4px 10px; border-radius: 12px; font-size: 0.65rem; font-weight: 600; font-family: Orbitron; margin-left: 8px;">RUN BACKTEST</span>'
    )

    st.markdown(
        f"""
        <div style="margin-bottom: 25px;">
            <div style="font-family: 'Orbitron'; font-size: 2.5rem; font-weight: 900; letter-spacing: 4px;
                background: linear-gradient(135deg, #22c55e 0%, #3b82f6 50%, #8b5cf6 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block;">
                GAMELOCK</div>
            <span style="font-family: 'Orbitron'; font-size: 2.5rem; font-weight: 300; color: #475569; margin-left: 10px;">AI</span>
            <span style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: #fff;
                padding: 6px 16px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;
                font-family: Orbitron; margin-left: 20px;">WEEK {current_week}</span>
            {ai_badge}
            {data_badge}
            <span class="pulse" style="display: inline-block; width: 8px; height: 8px;
                background: #22c55e; border-radius: 50%; margin-left: 15px;"></span>
            <span style="color: #22c55e; font-size: 0.75rem; margin-left: 5px; font-family: Orbitron;">LIVE</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_status:
    wins = metrics.get("wins", 0)
    losses = metrics.get("losses", 0)
    roi = metrics.get("roi", 0)

    st.markdown(
        f"""
        <div style="text-align: right; background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
            padding: 15px 20px; border-radius: 12px; border: 1px solid #334155;">
            <div style="font-family: Orbitron; font-size: 0.7rem; color: #64748b; letter-spacing: 2px;">BACKTEST RECORD</div>
            <div style="font-family: Orbitron; font-size: 1.5rem; font-weight: 800; color: #22c55e;">{wins}-{losses}</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">
                <span style="color: {'#22c55e' if roi > 0 else '#ef4444'}; font-weight: 700;">ROI {roi:.1f}%</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# TABS
# =============================================================================
tab_picks, tab_lab, tab_history, tab_live, tab_analysis = st.tabs(
    ["PICKS", "LAB", "HISTORY", "LIVE", "ANALYSIS"]
)


# =============================================================================
# TAB 1: TODAY'S PICKS
# =============================================================================
with tab_picks:
    # Format picks for display
    formatted_picks = format_picks_for_display(daily_picks, bet_history)

    if not formatted_picks:
        st.warning("⚠️ No picks available. Run prediction engine to generate new picks.")
        if st.button("🔄 Generate Predictions", type="primary"):
            with st.spinner("Generating predictions..."):
                result = generate_predictions()
                if result["success"]:
                    st.success(f"✅ Generated {len(result['picks'])} picks!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {result['error']}")
    else:
        # Summary metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("TODAY'S PICKS", len(formatted_picks))

        if formatted_picks:
            max_conf = max(p["Confidence"] for p in formatted_picks)
            best_pick = next(
                (p for p in formatted_picks if p["Confidence"] == max_conf), None
            )
            k2.metric(
                "TOP CONFIDENCE",
                f"{max_conf:.0f}%",
                best_pick["Pick"] if best_pick else "",
            )

            avg_ev = sum(p["EV"] for p in formatted_picks) / len(formatted_picks)
            k3.metric(
                "AVG EDGE", f"+{avg_ev:.1f}%", "POSITIVE" if avg_ev > 0 else "NEGATIVE"
            )

            high_conf = len([p for p in formatted_picks if p["Confidence"] >= 65])
            k4.metric("HIGH CONF PICKS", high_conf, f"≥65%")

        st.markdown("---")

        # Display each pick
        for pick in sorted(
            formatted_picks, key=lambda x: x["Confidence"], reverse=True
        ):
            conf_color = (
                "#22c55e"
                if pick["Confidence"] >= 70
                else "#f59e0b" if pick["Confidence"] >= 60 else "#ef4444"
            )
            ev_color = "#22c55e" if pick["EV"] > 0 else "#ef4444"

            st.markdown(
                f"""
            <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
                border: 1px solid #334155; border-left: 4px solid {conf_color};
                border-radius: 16px; padding: 24px; margin: 12px 0;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="color:#64748b; font-size:0.8rem; margin-bottom:6px; font-family:Orbitron;">{pick['Game']}</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#fff; font-family:Orbitron;">{pick['Pick']} {pick['Line']}</div>
                        <div style="color:#94a3b8; font-size:0.9rem; margin-top:8px;">
                            {pick['Type']} • <span style="color:{ev_color}; font-weight:700;">{pick['Odds']}</span>
                            {f" • <span style='color:#64748b;'>{pick['Book']}</span>" if pick.get('Book') else ""}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#64748b; font-size:0.65rem; font-family:Orbitron;">CONFIDENCE</div>
                        <div style="font-size:1.8rem; font-weight:800; color:{conf_color}; font-family:Orbitron;">{pick['Confidence']:.0f}%</div>
                        <div style="margin-top:10px;">
                            <div style="color:#64748b; font-size:0.65rem; font-family:Orbitron;">EDGE</div>
                            <div style="font-size:1.2rem; font-weight:700; color:{ev_color}; font-family:Orbitron;">+{pick['EV']:.1f}%</div>
                        </div>
                    </div>
                </div>
                <div style="height:6px; background:rgba(31,41,55,0.8); border-radius:3px; margin-top:18px;">
                    <div style="height:100%; width:{pick['Confidence']}%; background:{conf_color}; border-radius:3px;"></div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


# =============================================================================
# TAB 2: THE LAB
# =============================================================================
with tab_lab:
    # Real metrics from backtest
    m1, m2, m3, m4 = st.columns(4)

    total_bets = metrics.get("total_bets", 0)
    wins = metrics.get("wins", 0)
    losses = metrics.get("losses", 0)
    win_rate = metrics.get("win_rate", 0)
    roi = metrics.get("roi", 0)
    sharpe = metrics.get("sharpe_ratio", 0)
    max_dd = metrics.get("max_drawdown", 0)
    final_bank = metrics.get("final_bankroll", 500)

    m1.metric("BACKTEST RECORD", f"{wins}-{losses}", f"{win_rate:.1f}% Win Rate")
    m2.metric("ROI", f"{roi:.1f}%", "From $500 → ${:.0f}".format(final_bank))
    m3.metric("SHARPE RATIO", f"{sharpe:.2f}", "Risk-Adjusted")
    m4.metric("MAX DRAWDOWN", f"{abs(max_dd):.1f}%", "Peak to Trough")

    st.markdown("---")

    # Action buttons
    col_bt1, col_bt2, col_bt3 = st.columns(3)

    with col_bt1:
        if st.button("🔄 Run Backtest", type="primary", use_container_width=True):
            with st.spinner("Running backtest on historical data..."):
                result = run_backtest()
                if result["success"]:
                    st.success("✅ Backtest complete!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Backtest failed: {result['error']}")

    with col_bt2:
        if st.button("📊 Generate Predictions", use_container_width=True):
            with st.spinner("Generating predictions..."):
                result = generate_predictions()
                if result["success"]:
                    st.success(f"✅ Generated {len(result['picks'])} picks!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {result['error']}")

    with col_bt3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Charts
    if not bet_history.empty:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### EQUITY CURVE")
            fig1 = go.Figure()
            fig1.add_trace(
                go.Scatter(
                    x=bet_history["gameday"],
                    y=bet_history["bankroll"],
                    mode="lines+markers",
                    line=dict(color="#3b82f6", width=2),
                    marker=dict(size=4),
                    fill="tozeroy",
                    fillcolor="rgba(59,130,246,0.1)",
                )
            )
            fig1.add_hline(
                y=500,
                line_dash="dash",
                line_color="#64748b",
                annotation_text="Starting Bankroll",
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
                xaxis=dict(gridcolor="rgba(55,65,81,0.3)"),
                yaxis=dict(gridcolor="rgba(55,65,81,0.3)", title="Bankroll ($)"),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("#### WIN/LOSS DISTRIBUTION")
            results = bet_history["result"].value_counts()
            fig2 = go.Figure()
            fig2.add_trace(
                go.Bar(
                    x=["Wins", "Losses"],
                    y=[results.get("win", 0), results.get("loss", 0)],
                    marker_color=["#22c55e", "#ef4444"],
                )
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
                xaxis=dict(gridcolor="rgba(55,65,81,0.3)"),
                yaxis=dict(gridcolor="rgba(55,65,81,0.3)", title="Count"),
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("📊 Run a backtest to generate performance charts.")


# =============================================================================
# TAB 3: BET HISTORY
# =============================================================================
with tab_history:
    if not bet_history.empty:
        st.markdown("### 📜 Complete Bet History")

        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            result_filter = st.multiselect(
                "Filter by Result", ["win", "loss"], default=["win", "loss"]
            )
        with col_f2:
            year_filter = st.multiselect(
                "Filter by Year",
                sorted(bet_history["gameday"].dt.year.unique()),
                default=sorted(bet_history["gameday"].dt.year.unique()),
            )

        # Apply filters
        filtered = bet_history[
            (bet_history["result"].isin(result_filter))
            & (bet_history["gameday"].dt.year.isin(year_filter))
        ]

        # Display table
        display_df = filtered[
            [
                "gameday",
                "home_team",
                "away_team",
                "bet_size",
                "odds",
                "result",
                "profit",
                "bankroll",
            ]
        ].copy()
        display_df.columns = [
            "Date",
            "Home",
            "Away",
            "Bet Size",
            "Odds",
            "Result",
            "Profit",
            "Bankroll",
        ]
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        display_df["Bet Size"] = display_df["Bet Size"].apply(lambda x: f"${x:.0f}")
        display_df["Profit"] = display_df["Profit"].apply(
            lambda x: f"+${x:.0f}" if x > 0 else f"-${abs(x):.0f}"
        )
        display_df["Bankroll"] = display_df["Bankroll"].apply(lambda x: f"${x:.0f}")

        st.dataframe(display_df, use_container_width=True, height=500)

        # Summary stats
        st.markdown("---")
        st.markdown("### 📈 Summary Statistics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Bets", len(filtered))
        c2.metric("Win Rate", f"{(filtered['result'] == 'win').mean() * 100:.1f}%")
        c3.metric("Total Profit", f"${filtered['profit'].sum():.0f}")
        c4.metric("Avg Bet Size", f"${filtered['bet_size'].mean():.0f}")
    else:
        st.info("📊 No bet history available. Run a backtest to generate history.")


# =============================================================================
# TAB 4: LIVE ODDS
# =============================================================================
with tab_live:
    st.markdown("### 🔴 Live Odds")

    if not ODDS_API_KEY:
        st.warning(
            "⚠️ ODDS_API_KEY not configured. Set it in environment or Streamlit secrets."
        )
        st.markdown(
            """
        To enable live odds:
        1. Get a free API key at [the-odds-api.com](https://the-odds-api.com/)
        2. Set `ODDS_API_KEY` in your environment or `.streamlit/secrets.toml`
        """
        )
    else:
        if st.button("🔄 Fetch Live Odds"):
            with st.spinner("Fetching live odds from The Odds API..."):
                odds = get_live_odds()
                if odds:
                    st.success(f"✅ Loaded {len(odds)} games")

                    for game in odds[:10]:  # Show first 10
                        home = game.get("home_team", "Home")
                        away = game.get("away_team", "Away")
                        commence = game.get("commence_time", "")

                        st.markdown(
                            f"""
                        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155;
                            border-radius: 12px; padding: 16px; margin: 8px 0;">
                            <div style="font-weight: 700; color: #fff; font-size: 1.1rem;">{away} @ {home}</div>
                            <div style="color: #64748b; font-size: 0.8rem; margin-top: 4px;">{commence}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Show bookmaker odds
                        bookmakers = game.get("bookmakers", [])[:3]
                        if bookmakers:
                            cols = st.columns(len(bookmakers))
                            for i, book in enumerate(bookmakers):
                                with cols[i]:
                                    st.markdown(f"**{book.get('title', 'Book')}**")
                                    for market in book.get("markets", []):
                                        if market.get("key") == "h2h":
                                            outcomes = market.get("outcomes", [])
                                            for outcome in outcomes:
                                                team = outcome.get("name", "")
                                                price = outcome.get("price", 0)
                                                st.write(
                                                    f"{team}: {price:+d}"
                                                    if price > 0
                                                    else f"{team}: {price}"
                                                )
                else:
                    st.error("❌ Could not fetch odds")


# =============================================================================
# TAB 5: AI ANALYSIS
# =============================================================================
with tab_analysis:
    st.markdown("### 🤖 AI Analysis Studio")

    formatted_picks = format_picks_for_display(daily_picks, bet_history)

    if not formatted_picks:
        st.warning("No picks available for analysis. Generate predictions first.")
    else:
        # Select pick
        pick_options = [f"{p['Pick']} ({p['Game']})" for p in formatted_picks]
        selected_idx = st.selectbox(
            "Select a pick to analyze:",
            range(len(pick_options)),
            format_func=lambda x: pick_options[x],
        )
        selected_pick = formatted_picks[selected_idx]

        # Select AI provider
        providers = []
        if OPENAI_AVAILABLE and XAI_API_KEY:
            providers.append("grok")
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            providers.append("gpt")
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            providers.append("claude")
        if GENAI_AVAILABLE and GOOGLE_API_KEY:
            providers.append("gemini")

        if providers:
            ai_provider = st.selectbox("AI Provider:", providers, format_func=str.upper)

            if st.button("🎯 Generate Analysis", type="primary"):
                with st.spinner(f"Analyzing with {ai_provider.upper()}..."):
                    analysis, provider_used = generate_analysis(
                        selected_pick, provider=ai_provider
                    )

                    st.markdown(
                        f"""
                    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
                        border-left: 4px solid #6366f1; padding: 20px; border-radius: 12px; margin-top: 15px;">
                        <div style="color: #6366f1; font-weight: 600; font-size: 0.85rem; margin-bottom: 10px; font-family: Orbitron;">
                            AI ANALYSIS • {provider_used}
                        </div>
                        <div style="color: #e2e8f0; line-height: 1.7;">{analysis}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.warning(
                "No AI providers configured. Set API keys in environment or secrets."
            )
            st.markdown(
                """
            **Available providers:**
            - `XAI_API_KEY` → Grok (x.ai)
            - `OPENAI_API_KEY` → GPT-4
            - `ANTHROPIC_API_KEY` → Claude
            - `GOOGLE_API_KEY` → Gemini
            """
            )


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 20px;">
    <span style="font-family: Orbitron; letter-spacing: 2px;">GAMELOCK AI</span> • 
    Real Data • Real Predictions • Real Results
</div>
""",
    unsafe_allow_html=True,
)
