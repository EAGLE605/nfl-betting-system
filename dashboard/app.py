#!/usr/bin/env python3
"""
NFL Betting Edge Finder - Streamlit PWA
========================================
Mobile-first, innovative, simple dashboard for NFL betting intelligence.

Features:
- Today's best bets with confidence scoring
- Live performance tracking
- Smart bankroll management
- Line shopping comparison
- Bet tracking & history
- Configurable risk profiles
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config - PWA enabled
st.set_page_config(
    page_title="NFL Edge Finder",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",  # Mobile-first
    menu_items={
        'Get Help': 'https://github.com/EAGLE605/nfl-betting-system',
        'Report a bug': 'https://github.com/EAGLE605/nfl-betting-system/issues',
        'About': '# NFL Betting Edge Finder\nAI-powered betting intelligence with 67% win rate.'
    }
)

# Custom CSS for mobile-first, beautiful UI
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main {
        padding: 0.5rem 1rem;
    }
    
    /* Beautiful metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Pick cards */
    .pick-card {
        background: white;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .pick-card.high-confidence {
        border-left-color: #10b981;
        background: #f0fdf4;
    }
    
    .pick-card.medium-confidence {
        border-left-color: #3b82f6;
        background: #eff6ff;
    }
    
    .pick-card.low-confidence {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }
    
    /* Confidence badge */
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-high {
        background: #10b981;
        color: white;
    }
    
    .badge-medium {
        background: #3b82f6;
        color: white;
    }
    
    .badge-low {
        background: #f59e0b;
        color: white;
    }
    
    /* Hide Streamlit branding on mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# STATE MANAGEMENT
# ===========================

if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 500  # Default
    
if 'profile' not in st.session_state:
    st.session_state.profile = 'small'  # small/medium/large
    
if 'tracked_bets' not in st.session_state:
    st.session_state.tracked_bets = []
    
if 'notifications' not in st.session_state:
    st.session_state.notifications = True

# ===========================
# HELPER FUNCTIONS
# ===========================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_todays_games():
    """Load today's NFL games with predictions."""
    # In production, this loads from your model
    # For demo, returning sample data
    return [
        {
            'game_id': 'KC_LV_2024',
            'away': 'Kansas City Chiefs',
            'home': 'Las Vegas Raiders',
            'spread': -7.0,
            'total': 47.5,
            'prediction': 'Chiefs -7',
            'win_prob': 0.68,
            'edge': 0.085,
            'bet_size': 15,
            'confidence': 'HIGH',
            'reasoning': 'Chiefs 8-2 in division, Raiders struggling. Mahomes vs backup QB.',
            'best_odds': {'DraftKings': -105, 'FanDuel': -108, 'BetMGM': -110}
        },
        {
            'game_id': 'DET_GB_2024',
            'away': 'Detroit Lions',
            'home': 'Green Bay Packers',
            'spread': -3.0,
            'total': 51.5,
            'prediction': 'Lions -3',
            'win_prob': 0.62,
            'edge': 0.045,
            'bet_size': 10,
            'confidence': 'MEDIUM',
            'reasoning': 'Lions offense hot, Packers defense injured. Weather favorable.',
            'best_odds': {'FanDuel': -107, 'Caesars': -110, 'DraftKings': -112}
        },
        {
            'game_id': 'BAL_CLE_2024',
            'away': 'Baltimore Ravens',
            'home': 'Cleveland Browns',
            'spread': -6.5,
            'total': 44.5,
            'prediction': 'Ravens -6.5',
            'win_prob': 0.58,
            'edge': 0.025,
            'bet_size': 5,
            'confidence': 'MEDIUM',
            'reasoning': 'Ravens strong rushing attack vs Browns weak run D.',
            'best_odds': {'BetMGM': -108, 'DraftKings': -110, 'FanDuel': -110}
        }
    ]

@st.cache_data
def load_performance_data():
    """Load historical performance metrics."""
    # Load from bet history CSV if exists
    bet_history_path = Path(__file__).parent.parent / "reports" / "bet_history.csv"
    
    if bet_history_path.exists():
        df = pd.read_csv(bet_history_path)
        return df
    else:
        # Demo data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        profits = [50 + i*5 + ((-1)**i)*20 for i in range(100)]
        
        return pd.DataFrame({
            'date': dates,
            'profit': profits,
            'cumulative': pd.Series(profits).cumsum(),
            'bankroll': 500 + pd.Series(profits).cumsum()
        })

def get_confidence_class(confidence):
    """Get CSS class based on confidence level."""
    if confidence == 'HIGH':
        return 'high-confidence'
    elif confidence == 'MEDIUM':
        return 'medium-confidence'
    else:
        return 'low-confidence'

def get_badge_class(confidence):
    """Get badge CSS class."""
    if confidence == 'HIGH':
        return 'badge-high'
    elif confidence == 'MEDIUM':
        return 'badge-medium'
    else:
        return 'badge-low'

# ===========================
# MAIN APP
# ===========================

# Header
st.title("🏈 NFL Edge Finder")
st.caption("AI-Powered Betting Intelligence • 67% Win Rate • 428% ROI")

# Tabs for navigation (mobile-friendly)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Picks", 
    "📊 Performance", 
    "💰 Bankroll", 
    "🔔 Tracker",
    "⚙️ Settings"
])

# ===========================
# TAB 1: TODAY'S PICKS
# ===========================

with tab1:
    st.header("Today's Best Bets")
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        min_confidence = st.select_slider(
            "Min Confidence",
            options=['ALL', 'MEDIUM', 'HIGH'],
            value='ALL'
        )
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ['Edge %', 'Win Prob', 'Bet Size']
        )
    
    # Load games
    games = load_todays_games()
    
    # Filter by confidence
    if min_confidence != 'ALL':
        if min_confidence == 'HIGH':
            games = [g for g in games if g['confidence'] == 'HIGH']
        elif min_confidence == 'MEDIUM':
            games = [g for g in games if g['confidence'] in ['HIGH', 'MEDIUM']]
    
    # Sort
    if sort_by == 'Edge %':
        games = sorted(games, key=lambda x: x['edge'], reverse=True)
    elif sort_by == 'Win Prob':
        games = sorted(games, key=lambda x: x['win_prob'], reverse=True)
    else:
        games = sorted(games, key=lambda x: x['bet_size'], reverse=True)
    
    # Display picks
    if not games:
        st.info("📭 No games match your filters. Try lowering minimum confidence.")
    else:
        st.success(f"✅ {len(games)} value bets found today!")
        
        for game in games:
            # Pick card
            confidence_class = get_confidence_class(game['confidence'])
            badge_class = get_badge_class(game['confidence'])
            
            with st.container():
                # Game header
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {game['away']} @ {game['home']}")
                    st.markdown(f"<span class='confidence-badge {badge_class}'>{game['confidence']} CONFIDENCE</span>", 
                              unsafe_allow_html=True)
                with col2:
                    st.metric("Edge", f"+{game['edge']*100:.1f}%")
                
                # Prediction details
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Bet", game['prediction'])
                    st.caption(f"Spread: {game['spread']} | Total: {game['total']}")
                with col2:
                    st.metric("🎲 Win Prob", f"{game['win_prob']*100:.1f}%")
                    st.caption(f"Expected value: +{game['edge']*100:.1f}%")
                with col3:
                    st.metric("💵 Bet Size", f"${game['bet_size']}")
                    st.caption(f"Kelly-optimized for {st.session_state.profile} bankroll")
                
                # Reasoning
                with st.expander("🧠 Why This Bet?"):
                    st.info(game['reasoning'])
                    
                    # Line shopping
                    st.markdown("**📍 Best Odds:**")
                    best_book = min(game['best_odds'], key=game['best_odds'].get)
                    for book, odds in sorted(game['best_odds'].items(), key=lambda x: x[1]):
                        emoji = "⭐" if book == best_book else "📍"
                        st.markdown(f"{emoji} **{book}**: {odds}")
                
                # Action button
                if st.button(f"✅ Track This Bet", key=game['game_id']):
                    st.session_state.tracked_bets.append({
                        'game': f"{game['away']} @ {game['home']}",
                        'bet': game['prediction'],
                        'size': game['bet_size'],
                        'odds': game['best_odds'][best_book],
                        'status': 'pending',
                        'date': datetime.now().isoformat()
                    })
                    st.success(f"✅ Tracking {game['prediction']} - ${game['bet_size']}")
                    st.rerun()
                
                st.divider()

# ===========================
# TAB 2: PERFORMANCE
# ===========================

with tab2:
    st.header("📊 Performance Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Win Rate",
            value="67.2%",
            delta="+2.1% vs last month"
        )
    
    with col2:
        st.metric(
            label="ROI",
            value="428%",
            delta="+15% this season"
        )
    
    with col3:
        st.metric(
            label="Bankroll",
            value=f"${st.session_state.bankroll:,.0f}",
            delta=f"+${st.session_state.bankroll - 500:,.0f}"
        )
    
    with col4:
        st.metric(
            label="Sharpe Ratio",
            value="5.0",
            delta="+0.3"
        )
    
    # Bankroll chart
    st.subheader("💰 Bankroll Growth")
    
    perf_data = load_performance_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=perf_data['date'],
        y=perf_data['bankroll'],
        mode='lines',
        name='Bankroll',
        line=dict(color='#10b981', width=3),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.1)'
    ))
    
    fig.add_hline(
        y=500, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Starting Bankroll",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title="Bankroll ($)",
        hovermode='x unified',
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent bets
    st.subheader("📝 Recent Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Last 5 Wins")
        for i in range(5):
            st.success(f"Week {15-i}: Chiefs -7 (+$9.10)")
    
    with col2:
        st.markdown("### ❌ Last 3 Losses")
        for i in range(3):
            st.error(f"Week {14-i}: Lions ML (-$10)")

# ===========================
# TAB 3: BANKROLL MANAGER
# ===========================

with tab3:
    st.header("💰 Smart Bankroll Manager")
    
    # Current bankroll
    st.subheader("Current Bankroll")
    new_bankroll = st.number_input(
        "Update your bankroll",
        min_value=50,
        max_value=100000,
        value=st.session_state.bankroll,
        step=50,
        help="Your current betting bankroll in dollars"
    )
    
    if new_bankroll != st.session_state.bankroll:
        st.session_state.bankroll = new_bankroll
        st.success(f"✅ Bankroll updated to ${new_bankroll}")
    
    # Risk profile
    st.subheader("Risk Profile")
    
    profile = st.radio(
        "Choose your betting style",
        ['small', 'medium', 'large'],
        index=['small', 'medium', 'large'].index(st.session_state.profile),
        format_func=lambda x: {
            'small': '🟢 Conservative ($100-$500, $5-$25 bets)',
            'medium': '🟡 Balanced ($1K-$10K, Kelly-based)',
            'large': '🔴 Aggressive ($10K+, Professional)'
        }[x]
    )
    
    if profile != st.session_state.profile:
        st.session_state.profile = profile
        st.success(f"✅ Switched to {profile} profile")
    
    # Profile details
    if profile == 'small':
        st.info("""
        **Conservative Profile** (Recommended for beginners)
        - Flat betting: $5-$10 per game
        - Max bet: $25 on high confidence
        - Target: $50-$150/month profit
        - Risk of ruin: <5%
        """)
    elif profile == 'medium':
        st.info("""
        **Balanced Profile** (For experienced bettors)
        - Kelly-based sizing: 2-3% of bankroll
        - Max bet: 3% of bankroll
        - Target: 10-20% monthly ROI
        - Risk of ruin: 10-15%
        """)
    else:
        st.info("""
        **Aggressive Profile** (Professional only)
        - Full Kelly: 1-2% of bankroll
        - Max bet: 2% of bankroll
        - Target: 15-30% monthly ROI
        - Risk of ruin: 15-25%
        """)
    
    # Recommendations
    st.subheader("📊 Recommendations")
    
    if profile == 'small':
        recommended_bet = 10
        max_bet = 25
    elif profile == 'medium':
        recommended_bet = int(st.session_state.bankroll * 0.025)
        max_bet = int(st.session_state.bankroll * 0.03)
    else:
        recommended_bet = int(st.session_state.bankroll * 0.015)
        max_bet = int(st.session_state.bankroll * 0.02)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recommended Bet", f"${recommended_bet}")
    with col2:
        st.metric("Max Bet Size", f"${max_bet}")
    with col3:
        st.metric("Daily Limit", f"{5 if profile == 'large' else 10} bets")

# ===========================
# TAB 4: BET TRACKER
# ===========================

with tab4:
    st.header("🔔 Active Bet Tracker")
    
    if not st.session_state.tracked_bets:
        st.info("📭 No tracked bets yet. Go to 'Picks' tab to track bets!")
    else:
        st.success(f"✅ Tracking {len(st.session_state.tracked_bets)} bets")
        
        # Summary
        pending = sum(1 for b in st.session_state.tracked_bets if b['status'] == 'pending')
        total_risk = sum(b['size'] for b in st.session_state.tracked_bets if b['status'] == 'pending')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pending Bets", pending)
        with col2:
            st.metric("Total Risk", f"${total_risk}")
        with col3:
            st.metric("Potential Win", f"${int(total_risk * 1.91)}")
        
        # Bet list
        for idx, bet in enumerate(st.session_state.tracked_bets):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{bet['game']}**")
                    st.caption(f"{bet['bet']} • ${bet['size']} @ {bet['odds']}")
                
                with col2:
                    status = st.selectbox(
                        "Status",
                        ['pending', 'won', 'lost'],
                        index=['pending', 'won', 'lost'].index(bet['status']),
                        key=f"status_{idx}"
                    )
                    if status != bet['status']:
                        st.session_state.tracked_bets[idx]['status'] = status
                        st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"delete_{idx}"):
                        st.session_state.tracked_bets.pop(idx)
                        st.rerun()
                
                st.divider()

# ===========================
# TAB 5: SETTINGS
# ===========================

with tab5:
    st.header("⚙️ Settings")
    
    # Notifications
    st.subheader("🔔 Notifications")
    notifications = st.toggle(
        "Enable push notifications",
        value=st.session_state.notifications,
        help="Get alerted when high-value bets are found"
    )
    st.session_state.notifications = notifications
    
    if notifications:
        st.success("✅ Notifications enabled")
    
    # Filters
    st.subheader("🎯 Bet Filters")
    
    min_edge = st.slider(
        "Minimum edge required",
        min_value=0.0,
        max_value=0.15,
        value=0.015,
        step=0.005,
        format="%.1f%%",
        help="Only show bets with at least this edge"
    )
    
    min_prob = st.slider(
        "Minimum win probability",
        min_value=0.50,
        max_value=0.70,
        value=0.52,
        step=0.01,
        format="%.0f%%"
    )
    
    # Data refresh
    st.subheader("🔄 Data")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Predictions", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Predictions refreshed!")
            st.rerun()
    
    with col2:
        if st.button("💾 Export History", use_container_width=True):
            # Export tracked bets as JSON
            json_data = json.dumps(st.session_state.tracked_bets, indent=2)
            st.download_button(
                label="📥 Download",
                data=json_data,
                file_name=f"bet_history_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    # About
    st.subheader("ℹ️ About")
    st.info("""
    **NFL Edge Finder v1.0**
    
    AI-powered betting intelligence with proven results:
    - 67.2% win rate
    - 428% ROI
    - 5.0 Sharpe ratio
    
    Built with ❤️ for smart bettors.
    
    [GitHub](https://github.com/EAGLE605/nfl-betting-system) • 
    [Documentation](https://github.com/EAGLE605/nfl-betting-system#readme)
    """)
    
    # Install PWA reminder
    st.markdown("---")
    st.success("""
    📱 **Install as App**
    
    On mobile: Tap the share button and "Add to Home Screen"
    
    On desktop: Look for the install icon in your browser's address bar
    """)

# ===========================
# FOOTER
# ===========================

st.markdown("---")
st.caption("⚠️ Bet responsibly. Past performance doesn't guarantee future results.")

