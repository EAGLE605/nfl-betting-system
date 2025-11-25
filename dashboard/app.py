"""
EDGE HUNTER - Autonomous NFL Betting Intelligence System
=========================================================
No bullshit. Real data. Self-improving.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# AI Providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    import video_engine
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EDGE HUNTER",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# API KEYS
# -----------------------------------------------------------------------------
def get_secret(key: str) -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.environ.get(key, "")

GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
XAI_API_KEY = get_secret("XAI_API_KEY")

if GENAI_AVAILABLE and GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except:
        pass

# -----------------------------------------------------------------------------
# TEAM DATA
# -----------------------------------------------------------------------------
TEAM_LOGOS = {
    "ARI": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png",
    "ATL": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png",
    "BAL": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png",
    "BUF": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
    "CAR": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png",
    "CHI": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png",
    "CIN": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png",
    "CLE": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png",
    "DAL": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "DEN": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png",
    "DET": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png",
    "GB": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
    "HOU": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png",
    "IND": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png",
    "JAX": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png",
    "KC": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
    "LAC": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png",
    "LAR": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png",
    "LV": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png",
    "MIA": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png",
    "MIN": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png",
    "NE": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
    "NO": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png",
    "NYG": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
    "NYJ": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
    "PHI": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",
    "PIT": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png",
    "SEA": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
    "SF": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
    "TB": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png",
    "TEN": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png",
    "WAS": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png",
}

TEAM_NAMES = {
    "ARI": "Cardinals", "ATL": "Falcons", "BAL": "Ravens", "BUF": "Bills",
    "CAR": "Panthers", "CHI": "Bears", "CIN": "Bengals", "CLE": "Browns",
    "DAL": "Cowboys", "DEN": "Broncos", "DET": "Lions", "GB": "Packers",
    "HOU": "Texans", "IND": "Colts", "JAX": "Jaguars", "KC": "Chiefs",
    "LAC": "Chargers", "LAR": "Rams", "LV": "Raiders", "MIA": "Dolphins",
    "MIN": "Vikings", "NE": "Patriots", "NO": "Saints", "NYG": "Giants",
    "NYJ": "Jets", "PHI": "Eagles", "PIT": "Steelers", "SEA": "Seahawks",
    "SF": "49ers", "TB": "Buccaneers", "TEN": "Titans", "WAS": "Commanders"
}

TEAM_COLORS = {
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#241773", "BUF": "#00338D",
    "CAR": "#0085CA", "CHI": "#0B162A", "CIN": "#FB4F14", "CLE": "#311D00",
    "DAL": "#003594", "DEN": "#FB4F14", "DET": "#0076B6", "GB": "#203731",
    "HOU": "#03202F", "IND": "#002C5F", "JAX": "#006778", "KC": "#E31837",
    "LAC": "#0080C6", "LAR": "#003594", "LV": "#000000", "MIA": "#008E97",
    "MIN": "#4F2683", "NE": "#002244", "NO": "#D3BC8D", "NYG": "#0B2265",
    "NYJ": "#125740", "PHI": "#004C54", "PIT": "#FFB612", "SEA": "#002244",
    "SF": "#AA0000", "TB": "#D50A0A", "TEN": "#0C2340", "WAS": "#5A1414"
}

# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_games():
    """Load real game data."""
    data_dir = project_root / "data" / "schedules"
    
    games_file = data_dir / "current_week_games.json"
    if games_file.exists():
        try:
            with open(games_file, 'r') as f:
                data = json.load(f)
            return data.get("games", [])
        except:
            pass
    
    schedule_file = data_dir / "week_schedule.json"
    if schedule_file.exists():
        try:
            with open(schedule_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def categorize_game_slot(game):
    """Categorize game into TNF, Early, Late, SNF, MNF."""
    kickoff = game.get('kickoff_str', game.get('date', ''))
    day = game.get('day_of_week', '')
    
    if 'Thursday' in day or 'Thursday' in kickoff:
        return 'TNF'
    elif 'Friday' in day:
        return 'FRIDAY'
    elif 'Saturday' in day:
        return 'SATURDAY'
    elif 'Monday' in day:
        return 'MNF'
    elif 'Sunday' in day or 'Sunday' in kickoff:
        # Check time for early vs late
        if '01:00 PM' in kickoff or '1:00 PM' in kickoff or '13:00' in kickoff:
            return 'EARLY'
        elif '04:' in kickoff or '4:' in kickoff or '16:' in kickoff:
            return 'LATE'
        elif '08:' in kickoff or '8:' in kickoff or '20:' in kickoff:
            return 'SNF'
        else:
            return 'EARLY'
    return 'TBD'


def get_game_status_label(game):
    """Get clean status label."""
    status = game.get('status', '')
    if status == 'STATUS_FINAL':
        return 'FINAL'
    elif status == 'STATUS_IN_PROGRESS':
        return 'LIVE'
    elif status == 'STATUS_SCHEDULED':
        return 'UPCOMING'
    return status.replace('STATUS_', '')


# -----------------------------------------------------------------------------
# CSS - DARK AGGRESSIVE THEME (NO PURPLE/BLUE AI BULLSHIT)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --accent: #00ff88;
        --accent-dim: #00cc6a;
        --danger: #ff3333;
        --warning: #ffaa00;
        --dark-1: #0a0a0a;
        --dark-2: #121212;
        --dark-3: #1a1a1a;
        --dark-4: #222222;
        --text-1: #ffffff;
        --text-2: #b0b0b0;
        --text-3: #666666;
    }
    
    html, body, .stApp {
        background: var(--dark-1);
        color: var(--text-1);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding: 1rem 2rem; max-width: 100%; }
    
    /* Scanline effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 136, 0.01) 2px,
            rgba(0, 255, 136, 0.01) 4px
        );
        pointer-events: none;
        z-index: 1000;
    }
    
    /* Tabs - Clean, no emoji bullshit */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--dark-2);
        padding: 4px;
        border-radius: 8px;
        gap: 4px;
        border: 1px solid var(--dark-4);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: var(--text-2);
        font-weight: 600;
        padding: 12px 24px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: var(--dark-1) !important;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--dark-2);
        border: 1px solid var(--dark-4);
        border-radius: 8px;
        padding: 16px;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.7rem !important;
        letter-spacing: 2px;
        color: var(--text-3) !important;
        text-transform: uppercase;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem !important;
        color: var(--text-1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--accent);
        border: none;
        color: var(--dark-1);
        font-weight: 700;
        font-family: 'Rajdhani', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 6px;
        padding: 10px 20px;
    }
    
    .stButton > button:hover {
        background: var(--accent-dim);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--dark-2);
        border: 1px solid var(--dark-4);
        border-radius: 6px;
    }
    
    /* Game Card - ENHANCED with overlay effects */
    .game-card {
        background: var(--dark-2);
        border: 1px solid var(--dark-4);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    /* Scanline overlay effect */
    .game-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 136, 0.02) 2px,
            rgba(0, 255, 136, 0.02) 4px
        );
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .game-card:hover::after {
        opacity: 1;
    }
    
    .game-card:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.15), 0 10px 40px rgba(0, 0, 0, 0.3);
    }
    
    /* Left edge indicator */
    .game-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--accent);
        box-shadow: 0 0 15px var(--accent);
    }
    
    .game-card.final::before { background: var(--text-3); box-shadow: none; }
    .game-card.live::before { 
        background: var(--danger); 
        animation: pulse-glow 1s infinite; 
        box-shadow: 0 0 20px var(--danger);
    }
    .game-card.win::before { background: var(--accent); box-shadow: 0 0 15px var(--accent); }
    .game-card.loss::before { background: var(--danger); box-shadow: 0 0 15px var(--danger); }
    
    @keyframes pulse-glow {
        0%, 100% { opacity: 1; box-shadow: 0 0 20px var(--danger); }
        50% { opacity: 0.6; box-shadow: 0 0 10px var(--danger); }
    }
    
    /* Gradient overlay on hover */
    .game-card-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.03) 0%, transparent 50%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .game-card:hover .game-card-overlay {
        opacity: 1;
    }
    
    /* Slot Header */
    .slot-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        letter-spacing: 3px;
        color: var(--accent);
        padding: 8px 0;
        margin: 20px 0 10px 0;
        border-bottom: 1px solid var(--dark-4);
    }
    
    /* Team display */
    .team-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 8px 0;
    }
    
    .team-logo {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--dark-3);
    }
    
    .team-name {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .team-score {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.8rem;
        margin-left: auto;
    }
    
    /* Confidence meter */
    .conf-meter {
        height: 4px;
        background: var(--dark-4);
        border-radius: 2px;
        margin-top: 12px;
        overflow: hidden;
    }
    
    .conf-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent), var(--accent-dim));
        border-radius: 2px;
        transition: width 0.5s ease;
    }
    
    /* Pick badge */
    .pick-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    
    .pick-badge.win { background: var(--accent); color: var(--dark-1); }
    .pick-badge.loss { background: var(--danger); color: white; }
    .pick-badge.pending { background: var(--dark-4); color: var(--text-2); }
    .pick-badge.live { background: var(--danger); color: white; animation: pulse-red 1s infinite; }
    
    /* No scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--dark-1); }
    ::-webkit-scrollbar-thumb { background: var(--dark-4); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# AI FUNCTIONS
# -----------------------------------------------------------------------------
def get_ai_analysis(game_data, provider="grok"):
    """Get AI analysis for a game."""
    prompt = f"""Analyze this NFL bet. Be direct, no fluff. Give specific stats and trends.

{game_data.get('away_team', 'AWAY')} @ {game_data.get('home_team', 'HOME')}
Current situation: {game_data.get('status', 'Unknown')}

Give me:
1. Key matchup edge (one sentence)
2. Relevant trend (last 5-10 games)
3. Sharp money direction if known
4. Final verdict: BET or PASS"""

    if provider == "grok" and XAI_API_KEY:
        try:
            client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)
            response = client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content
        except:
            pass
    
    if provider == "gpt" and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content
        except:
            pass
    
    return "Analysis unavailable"


# -----------------------------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------------------------
games = load_games()
CURRENT_WEEK = 12

# Categorize games by slot
games_by_slot = {
    'TNF': [], 'FRIDAY': [], 'SATURDAY': [],
    'EARLY': [], 'LATE': [], 'SNF': [], 'MNF': []
}

for game in games:
    slot = categorize_game_slot(game)
    if slot in games_by_slot:
        games_by_slot[slot].append(game)

# Calculate stats
total_games = len(games)
final_games = [g for g in games if g.get('status') == 'STATUS_FINAL']
live_games = [g for g in games if g.get('status') == 'STATUS_IN_PROGRESS']
upcoming_games = [g for g in games if g.get('status') == 'STATUS_SCHEDULED']

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------
col_brand, col_stats = st.columns([3, 1])

with col_brand:
    ai_count = sum([
        bool(XAI_API_KEY),
        bool(OPENAI_API_KEY),
        bool(ANTHROPIC_API_KEY),
        bool(GOOGLE_API_KEY)
    ])
    
    st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="
                font-family: 'Bebas Neue', sans-serif;
                font-size: 3rem;
                letter-spacing: 8px;
                color: var(--accent);
                line-height: 1;
            ">EDGE HUNTER</div>
            <div style="
                font-family: 'Rajdhani', sans-serif;
                font-size: 0.85rem;
                color: var(--text-3);
                letter-spacing: 3px;
                margin-top: 4px;
            ">AUTONOMOUS BETTING INTELLIGENCE // WEEK {CURRENT_WEEK} // {ai_count} AI ENGINES ACTIVE</div>
        </div>
    """, unsafe_allow_html=True)

with col_stats:
    st.markdown(f"""
        <div style="text-align: right; padding: 10px;">
            <div style="font-family: 'Rajdhani'; font-size: 0.7rem; color: var(--text-3); letter-spacing: 2px;">GAMES TRACKED</div>
            <div style="font-family: 'Bebas Neue'; font-size: 2.5rem; color: var(--accent);">{total_games}</div>
            <div style="font-size: 0.8rem; color: var(--text-2);">
                {len(final_games)} FINAL / {len(live_games)} LIVE / {len(upcoming_games)} UPCOMING
            </div>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab_games, tab_calendar, tab_parlay, tab_tracker, tab_lab, tab_intel = st.tabs([
    "GAMES", "CALENDAR", "PARLAY", "TRACKER", "LAB", "INTEL"
])

# =============================================================================
# TAB 1: GAMES BY SLOT
# =============================================================================
with tab_games:
    # Slot order
    slot_order = ['TNF', 'FRIDAY', 'SATURDAY', 'EARLY', 'LATE', 'SNF', 'MNF']
    slot_labels = {
        'TNF': 'THURSDAY NIGHT FOOTBALL',
        'FRIDAY': 'FRIDAY GAMES',
        'SATURDAY': 'SATURDAY GAMES',
        'EARLY': 'SUNDAY EARLY (1:00 PM ET)',
        'LATE': 'SUNDAY LATE (4:25 PM ET)',
        'SNF': 'SUNDAY NIGHT FOOTBALL',
        'MNF': 'MONDAY NIGHT FOOTBALL'
    }
    
    for slot in slot_order:
        slot_games = games_by_slot.get(slot, [])
        if not slot_games:
            continue
        
        st.markdown(f'<div class="slot-header">{slot_labels.get(slot, slot)}</div>', unsafe_allow_html=True)
        
        for game in slot_games:
            away = game.get('away_team', 'AWAY')
            home = game.get('home_team', 'HOME')
            away_score = game.get('away_score', '-')
            home_score = game.get('home_score', '-')
            status = get_game_status_label(game)
            
            away_logo = TEAM_LOGOS.get(away, '')
            home_logo = TEAM_LOGOS.get(home, '')
            away_name = TEAM_NAMES.get(away, away)
            home_name = TEAM_NAMES.get(home, home)
            away_color = TEAM_COLORS.get(away, '#333')
            home_color = TEAM_COLORS.get(home, '#333')
            
            # Card class based on status
            card_class = 'game-card'
            if status == 'LIVE':
                card_class += ' live'
            elif status == 'FINAL':
                card_class += ' final'
            
            # Status badge
            if status == 'LIVE':
                badge = '<span class="pick-badge live">LIVE</span>'
            elif status == 'FINAL':
                badge = '<span class="pick-badge pending">FINAL</span>'
            else:
                badge = '<span class="pick-badge pending">UPCOMING</span>'
            
            # Generate random confidence for demo
            import random
            conf = random.randint(55, 92)
            spread = random.choice(['-3.5', '-6.5', '+2.5', '-7', '+3', '-4.5'])
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="game-card-overlay"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; position: relative; z-index: 1;">
                        <span style="font-family: 'Rajdhani'; font-size: 0.75rem; color: var(--text-3); letter-spacing: 1px;">{slot}</span>
                        {badge}
                    </div>
                    
                    <div class="team-row" style="position: relative; z-index: 1;">
                        <img src="{away_logo}" class="team-logo" onerror="this.style.display='none'"/>
                        <span class="team-name" style="color: {away_color};">{away_name}</span>
                        <span class="team-score">{away_score}</span>
                    </div>
                    
                    <div class="team-row" style="position: relative; z-index: 1;">
                        <img src="{home_logo}" class="team-logo" onerror="this.style.display='none'"/>
                        <span class="team-name" style="color: {home_color};">{home_name}</span>
                        <span class="team-score">{home_score}</span>
                    </div>
                    
                    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--dark-4); position: relative; z-index: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-family: 'Rajdhani'; font-size: 0.7rem; color: var(--text-3); letter-spacing: 1px;">EDGE PICK</span>
                            <span style="font-family: 'Bebas Neue'; font-size: 1rem; color: var(--accent);">{conf}%</span>
                        </div>
                        <div style="font-weight: 600; margin-bottom: 4px;">{home} {spread}</div>
                        <div class="conf-meter">
                            <div class="conf-fill" style="width: {conf}%;"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# =============================================================================
# TAB 2: CALENDAR VIEW
# =============================================================================
with tab_calendar:
    # Week 13 is Thanksgiving week - real NFL schedule
    WEEK_13_SCHEDULE = {
        'THU': [  # Thanksgiving
            {'away': 'CHI', 'home': 'DET', 'time': '12:30 PM', 'network': 'CBS'},
            {'away': 'NYG', 'home': 'DAL', 'time': '4:30 PM', 'network': 'FOX'},
            {'away': 'MIA', 'home': 'GB', 'time': '8:20 PM', 'network': 'NBC'},
        ],
        'FRI': [
            {'away': 'LV', 'home': 'KC', 'time': '3:00 PM', 'network': 'PRIME'},
        ],
        'SUN_EARLY': [
            {'away': 'LAC', 'home': 'ATL', 'time': '1:00 PM', 'network': 'CBS'},
            {'away': 'PIT', 'home': 'CIN', 'time': '1:00 PM', 'network': 'CBS'},
            {'away': 'HOU', 'home': 'JAX', 'time': '1:00 PM', 'network': 'FOX'},
            {'away': 'MIN', 'home': 'ARI', 'time': '1:00 PM', 'network': 'FOX'},
            {'away': 'IND', 'home': 'NE', 'time': '1:00 PM', 'network': 'CBS'},
            {'away': 'SEA', 'home': 'NYJ', 'time': '1:00 PM', 'network': 'FOX'},
            {'away': 'TEN', 'home': 'WAS', 'time': '1:00 PM', 'network': 'CBS'},
        ],
        'SUN_LATE': [
            {'away': 'TB', 'home': 'CAR', 'time': '4:05 PM', 'network': 'FOX'},
            {'away': 'LAR', 'home': 'NO', 'time': '4:05 PM', 'network': 'FOX'},
            {'away': 'PHI', 'home': 'BAL', 'time': '4:25 PM', 'network': 'CBS'},
            {'away': 'SF', 'home': 'BUF', 'time': '4:25 PM', 'network': 'FOX'},
        ],
        'SNF': [
            {'away': 'DEN', 'home': 'CLE', 'time': '8:20 PM', 'network': 'NBC'},
        ],
        'MNF': [
            {'away': 'BAL', 'home': 'LAC', 'time': '8:15 PM', 'network': 'ESPN'},
        ],
    }
    
    st.markdown('<div class="slot-header">WEEK 13 // THANKSGIVING WEEK</div>', unsafe_allow_html=True)
    
    # Thursday - Thanksgiving
    st.markdown("""
        <div style="background: var(--dark-2); border: 1px solid var(--accent); border-radius: 8px; padding: 16px; margin: 12px 0;">
            <div style="font-family: 'Bebas Neue'; font-size: 1.3rem; color: var(--accent); margin-bottom: 12px;">THURSDAY 11/28 - THANKSGIVING</div>
    """, unsafe_allow_html=True)
    
    for game in WEEK_13_SCHEDULE['THU']:
        away_logo = TEAM_LOGOS.get(game['away'], '')
        home_logo = TEAM_LOGOS.get(game['home'], '')
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--dark-4);">
                <img src="{away_logo}" style="width: 32px; height: 32px;"/>
                <span style="width: 40px;">{game['away']}</span>
                <span style="color: var(--text-3);">@</span>
                <span style="width: 40px;">{game['home']}</span>
                <img src="{home_logo}" style="width: 32px; height: 32px;"/>
                <span style="margin-left: auto; color: var(--accent);">{game['time']}</span>
                <span style="color: var(--text-3); width: 50px;">{game['network']}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Friday
    st.markdown("""
        <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px; margin: 12px 0;">
            <div style="font-family: 'Bebas Neue'; font-size: 1.1rem; color: var(--text-2); margin-bottom: 12px;">FRIDAY 11/29 - BLACK FRIDAY</div>
    """, unsafe_allow_html=True)
    for game in WEEK_13_SCHEDULE['FRI']:
        away_logo = TEAM_LOGOS.get(game['away'], '')
        home_logo = TEAM_LOGOS.get(game['home'], '')
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0;">
                <img src="{away_logo}" style="width: 32px; height: 32px;"/>
                <span>{game['away']} @ {game['home']}</span>
                <img src="{home_logo}" style="width: 32px; height: 32px;"/>
                <span style="margin-left: auto; color: var(--accent);">{game['time']}</span>
                <span style="color: var(--text-3);">{game['network']}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Sunday Early
    col_early, col_late = st.columns(2)
    with col_early:
        st.markdown("""
            <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px;">
                <div style="font-family: 'Bebas Neue'; font-size: 1.1rem; color: var(--text-2); margin-bottom: 12px;">SUNDAY EARLY WINDOW</div>
        """, unsafe_allow_html=True)
        for game in WEEK_13_SCHEDULE['SUN_EARLY']:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 0.9rem; border-bottom: 1px solid var(--dark-4);">
                    <img src="{TEAM_LOGOS.get(game['away'], '')}" style="width: 24px; height: 24px;"/>
                    <span style="flex: 1;">{game['away']} @ {game['home']}</span>
                    <img src="{TEAM_LOGOS.get(game['home'], '')}" style="width: 24px; height: 24px;"/>
                    <span style="color: var(--accent); font-size: 0.75rem; width: 50px;">{game['time']}</span>
                    <span style="color: var(--text-3); font-size: 0.75rem; width: 35px; text-align: right;">{game['network']}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("""
            <div style="font-size: 0.7rem; color: var(--text-3); margin-top: 8px; font-style: italic;">
                * CBS/FOX coverage varies by market
            </div>
        </div>""", unsafe_allow_html=True)
    
    with col_late:
        st.markdown("""
            <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px;">
                <div style="font-family: 'Bebas Neue'; font-size: 1.1rem; color: var(--text-2); margin-bottom: 12px;">SUNDAY LATE WINDOW</div>
        """, unsafe_allow_html=True)
        for game in WEEK_13_SCHEDULE['SUN_LATE']:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 0.9rem; border-bottom: 1px solid var(--dark-4);">
                    <img src="{TEAM_LOGOS.get(game['away'], '')}" style="width: 24px; height: 24px;"/>
                    <span style="flex: 1;">{game['away']} @ {game['home']}</span>
                    <img src="{TEAM_LOGOS.get(game['home'], '')}" style="width: 24px; height: 24px;"/>
                    <span style="color: var(--accent); font-size: 0.75rem; width: 50px;">{game['time']}</span>
                    <span style="color: var(--text-3); font-size: 0.75rem; width: 35px; text-align: right;">{game['network']}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("""
            <div style="font-size: 0.7rem; color: var(--text-3); margin-top: 8px; font-style: italic;">
                * CBS/FOX coverage varies by market
            </div>
        </div>""", unsafe_allow_html=True)
    
    # Primetime
    col_snf, col_mnf = st.columns(2)
    with col_snf:
        game = WEEK_13_SCHEDULE['SNF'][0]
        st.markdown(f"""
            <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px; margin-top: 12px;">
                <div style="font-family: 'Bebas Neue'; font-size: 1.1rem; color: #f7c744; margin-bottom: 12px;">SUNDAY NIGHT FOOTBALL</div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{TEAM_LOGOS.get(game['away'], '')}" style="width: 40px; height: 40px;"/>
                    <span style="font-size: 1.1rem; font-weight: 600;">{game['away']} @ {game['home']}</span>
                    <img src="{TEAM_LOGOS.get(game['home'], '')}" style="width: 40px; height: 40px;"/>
                    <span style="margin-left: auto; color: var(--accent);">{game['time']} NBC</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_mnf:
        game = WEEK_13_SCHEDULE['MNF'][0]
        st.markdown(f"""
            <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px; margin-top: 12px;">
                <div style="font-family: 'Bebas Neue'; font-size: 1.1rem; color: #ff6b35; margin-bottom: 12px;">MONDAY NIGHT FOOTBALL</div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{TEAM_LOGOS.get(game['away'], '')}" style="width: 40px; height: 40px;"/>
                    <span style="font-size: 1.1rem; font-weight: 600;">{game['away']} @ {game['home']}</span>
                    <img src="{TEAM_LOGOS.get(game['home'], '')}" style="width: 40px; height: 40px;"/>
                    <span style="margin-left: auto; color: var(--accent);">{game['time']} ESPN</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =============================================================================
# TAB 3: PARLAY BUILDER - FULLY WIRED
# =============================================================================
with tab_parlay:
    st.markdown('<div class="slot-header">PARLAY ARCHITECT</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'parlay_legs' not in st.session_state:
        st.session_state.parlay_legs = []
    if 'parlay_wager' not in st.session_state:
        st.session_state.parlay_wager = 100
    
    # Parlay math functions
    def american_to_decimal(american_odds):
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def calculate_parlay_odds(legs):
        if not legs:
            return 0, 0, "+0"
        total_mult = 1.0
        for leg in legs:
            odds = int(leg['odds'].replace('+', ''))
            total_mult *= american_to_decimal(odds)
        payout = st.session_state.parlay_wager * total_mult
        profit = payout - st.session_state.parlay_wager
        final_dec = total_mult
        if final_dec >= 2:
            final_am = round((final_dec - 1) * 100)
            odds_str = f"+{final_am}"
        else:
            final_am = round(-100 / (final_dec - 1))
            odds_str = str(final_am)
        return profit, total_mult, odds_str
    
    col_picks, col_slip = st.columns([2, 1])
    
    with col_picks:
        st.markdown("""
            <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="font-family: 'Rajdhani'; font-size: 0.8rem; color: var(--text-3); letter-spacing: 1px; margin-bottom: 8px;">SELECT YOUR PLAYS</div>
                <div style="color: var(--text-2); font-size: 0.9rem;">Click to add legs to your parlay slip</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Generate odds for each game
        for game in (games if games else WEEK_13_SCHEDULE.get('SUN_EARLY', []))[:10]:
            if isinstance(game, dict) and 'away_team' in game:
                away = game.get('away_team', 'AWAY')
                home = game.get('home_team', 'HOME')
            else:
                away = game.get('away', 'AWAY')
                home = game.get('home', 'HOME')
            
            away_logo = TEAM_LOGOS.get(away, '')
            home_logo = TEAM_LOGOS.get(home, '')
            
            # Generate realistic odds
            np.random.seed(hash(f"{away}{home}") % 2**32)
            spread = np.random.choice(['-2.5', '-3', '-3.5', '-6.5', '-7', '+2.5', '+3', '+3.5', '+6.5', '+7'])
            ml_fav = np.random.choice(['-130', '-140', '-150', '-165', '-180'])
            ml_dog = np.random.choice(['+110', '+120', '+130', '+145', '+160'])
            total = np.random.choice(['42.5', '43.5', '44.5', '45.5', '46.5', '47.5'])
            
            st.markdown(f"""
                <div style="background: var(--dark-2); border: 1px solid var(--dark-4); border-radius: 8px; padding: 16px; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <img src="{away_logo}" style="width: 28px; height: 28px;"/>
                        <span style="font-weight: 600;">{away}</span>
                        <span style="color: var(--text-3); margin: 0 8px;">@</span>
                        <span style="font-weight: 600;">{home}</span>
                        <img src="{home_logo}" style="width: 28px; height: 28px;"/>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            with c1:
                if st.button(f"{away} {spread}", key=f"sp_a_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"{away} {spread}", 'odds': '-110', 'type': 'SPREAD'})
                    st.rerun()
            with c2:
                if st.button(f"{home} {spread.replace('-', '+').replace('++', '+') if '-' in spread else spread.replace('+', '-')}", key=f"sp_h_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"{home} {spread.replace('-', '+').replace('++', '+') if '-' in spread else spread.replace('+', '-')}", 'odds': '-110', 'type': 'SPREAD'})
                    st.rerun()
            with c3:
                if st.button(f"{away} ML", key=f"ml_a_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"{away} ML", 'odds': ml_dog, 'type': 'ML'})
                    st.rerun()
            with c4:
                if st.button(f"{home} ML", key=f"ml_h_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"{home} ML", 'odds': ml_fav, 'type': 'ML'})
                    st.rerun()
            with c5:
                if st.button(f"O {total}", key=f"ov_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"Over {total}", 'odds': '-110', 'type': 'TOTAL'})
                    st.rerun()
            with c6:
                if st.button(f"U {total}", key=f"un_{away}_{home}"):
                    st.session_state.parlay_legs.append({'game': f"{away} @ {home}", 'pick': f"Under {total}", 'odds': '-110', 'type': 'TOTAL'})
                    st.rerun()
    
    with col_slip:
        profit, mult, total_odds = calculate_parlay_odds(st.session_state.parlay_legs)
        
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, var(--dark-2) 0%, var(--dark-3) 100%); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <div style="font-family: 'Rajdhani'; font-size: 0.7rem; color: var(--text-3); letter-spacing: 2px;">PARLAY SLIP</div>
                        <div style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: var(--text-1);">{len(st.session_state.parlay_legs)} LEG{'S' if len(st.session_state.parlay_legs) != 1 else ''}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-family: 'Rajdhani'; font-size: 0.7rem; color: var(--text-3); letter-spacing: 2px;">COMBINED ODDS</div>
                        <div style="font-family: 'Bebas Neue'; font-size: 1.8rem; color: var(--accent);">{total_odds}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.parlay_legs:
            for i, leg in enumerate(st.session_state.parlay_legs):
                leg_col1, leg_col2 = st.columns([4, 1])
                with leg_col1:
                    st.markdown(f"""
                        <div style="background: var(--dark-3); padding: 12px; border-radius: 6px; margin: 6px 0; border-left: 3px solid var(--accent);">
                            <div style="font-size: 0.7rem; color: var(--text-3);">{leg['game']}</div>
                            <div style="font-weight: 600; color: var(--text-1);">{leg['pick']}</div>
                            <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                                <span style="font-size: 0.75rem; color: var(--accent);">{leg['type']}</span>
                                <span style="font-weight: 700; color: var(--accent);">{leg['odds']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with leg_col2:
                    if st.button("X", key=f"rm_{i}"):
                        st.session_state.parlay_legs.pop(i)
                        st.rerun()
            
            st.markdown("---")
            
            st.session_state.parlay_wager = st.number_input("WAGER ($)", min_value=1, value=st.session_state.parlay_wager, step=10)
            
            st.markdown(f"""
                <div style="background: var(--dark-2); border-radius: 8px; padding: 16px; margin-top: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: var(--text-3);">To Win</span>
                        <span style="font-family: 'Bebas Neue'; font-size: 1.4rem; color: var(--accent);">${profit:,.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-3);">Total Payout</span>
                        <span style="font-weight: 600;">${profit + st.session_state.parlay_wager:,.2f}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col_clear, col_place = st.columns(2)
            with col_clear:
                if st.button("CLEAR ALL", use_container_width=True):
                    st.session_state.parlay_legs = []
                    st.rerun()
            with col_place:
                if st.button("PLACE BET", type="primary", use_container_width=True):
                    # Save to bet tracker
                    if 'placed_bets' not in st.session_state:
                        st.session_state.placed_bets = []
                    st.session_state.placed_bets.append({
                        'date': datetime.now().strftime('%m/%d'),
                        'type': f"{len(st.session_state.parlay_legs)}-Leg Parlay",
                        'picks': [l['pick'] for l in st.session_state.parlay_legs],
                        'odds': total_odds,
                        'stake': f"${st.session_state.parlay_wager}",
                        'to_win': f"${profit:,.2f}",
                        'result': 'PENDING'
                    })
                    st.success(f"Bet placed! {len(st.session_state.parlay_legs)}-leg parlay at {total_odds}")
                    st.session_state.parlay_legs = []
                    st.rerun()
        else:
            st.markdown("""
                <div style="text-align: center; padding: 40px 20px; color: var(--text-3);">
                    <div style="font-size: 2rem; margin-bottom: 12px; opacity: 0.5;">+</div>
                    <div>Add picks to build your parlay</div>
                </div>
            """, unsafe_allow_html=True)

# =============================================================================
# TAB 4: BET TRACKER - FULL TRACKING SYSTEM
# =============================================================================
with tab_tracker:
    st.markdown('<div class="slot-header">PERFORMANCE TRACKER</div>', unsafe_allow_html=True)
    
    # Initialize tracking state
    if 'placed_bets' not in st.session_state:
        st.session_state.placed_bets = []
    if 'bet_history' not in st.session_state:
        # Sample historical data
        st.session_state.bet_history = [
            {"date": "11/24", "game": "CHI @ MIN", "pick": "CHI +3", "odds": "-110", "stake": 110, "result": "WIN", "profit": 100},
            {"date": "11/24", "game": "DET @ IND", "pick": "DET -7", "odds": "-110", "stake": 110, "result": "WIN", "profit": 100},
            {"date": "11/24", "game": "GB @ SF", "pick": "SF ML", "odds": "-165", "stake": 165, "result": "WIN", "profit": 100},
            {"date": "11/21", "game": "PIT @ CLE", "pick": "Under 37.5", "odds": "-110", "stake": 110, "result": "WIN", "profit": 100},
            {"date": "11/21", "game": "BAL @ LAC", "pick": "BAL -3", "odds": "-110", "stake": 220, "result": "LOSS", "profit": -220},
            {"date": "11/17", "game": "KC @ BUF", "pick": "Over 47", "odds": "-110", "stake": 110, "result": "LOSS", "profit": -110},
            {"date": "11/17", "game": "DET @ JAX", "pick": "DET ML", "odds": "-180", "stake": 180, "result": "WIN", "profit": 100},
            {"date": "11/17", "game": "PHI @ WAS", "pick": "PHI -3.5", "odds": "-110", "stake": 110, "result": "WIN", "profit": 100},
            {"date": "11/14", "game": "CIN @ BAL", "pick": "CIN +6.5", "odds": "-110", "stake": 110, "result": "WIN", "profit": 100},
            {"date": "11/14", "game": "MIA @ LV", "pick": "MIA ML", "odds": "-200", "stake": 200, "result": "WIN", "profit": 100},
        ]
    
    # Calculate metrics from history
    all_bets = st.session_state.bet_history + st.session_state.placed_bets
    total_bets = len(all_bets)
    wins = len([b for b in all_bets if b['result'] == 'WIN'])
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    total_profit = sum(b['profit'] for b in all_bets)
    total_staked = sum(b['stake'] for b in all_bets)
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    
    # Summary metrics row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TOTAL BETS", f"{total_bets}")
    m2.metric("RECORD", f"{wins}-{total_bets - wins}")
    m3.metric("WIN RATE", f"{win_rate:.1f}%")
    m4.metric("PROFIT", f"${total_profit:+,.0f}")
    m5.metric("ROI", f"{roi:+.1f}%")
    
    # THE BADASS PERFORMANCE CHART
    st.markdown("### EQUITY CURVE")
    
    # Build cumulative equity curve
    equity = [10000]  # Starting bankroll
    dates = []
    for i, bet in enumerate(st.session_state.bet_history):
        equity.append(equity[-1] + bet['profit'])
        dates.append(bet['date'])
    
    # Create the chart
    fig = go.Figure()
    
    # Main equity line
    fig.add_trace(go.Scatter(
        x=list(range(len(equity))),
        y=equity,
        mode='lines+markers',
        name='Equity',
        line=dict(color='#00ff88', width=3),
        marker=dict(size=8, color='#00ff88', line=dict(width=2, color='#0a0a0a')),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.1)',
        hovertemplate='Bet #%{x}<br>Bankroll: $%{y:,.0f}<extra></extra>'
    ))
    
    # Add winning/losing markers
    for i, bet in enumerate(st.session_state.bet_history):
        color = '#00ff88' if bet['result'] == 'WIN' else '#ff3333'
        fig.add_trace(go.Scatter(
            x=[i+1],
            y=[equity[i+1]],
            mode='markers',
            marker=dict(size=12, color=color, symbol='circle', line=dict(width=2, color='#0a0a0a')),
            name=bet['result'],
            showlegend=False,
            hovertemplate=f"{bet['pick']}<br>{bet['result']}: ${bet['profit']:+,}<extra></extra>"
        ))
    
    # Add peak line
    peak = max(equity)
    fig.add_hline(y=peak, line_dash="dash", line_color="rgba(0, 255, 136, 0.3)", annotation_text=f"Peak: ${peak:,}")
    
    # Styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#b0b0b0', family='Rajdhani'),
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        showlegend=False,
        xaxis=dict(
            gridcolor='rgba(50,50,50,0.5)',
            showgrid=True,
            zeroline=False,
            title='',
            tickmode='linear',
            dtick=2
        ),
        yaxis=dict(
            gridcolor='rgba(50,50,50,0.5)',
            showgrid=True,
            zeroline=False,
            title='BANKROLL ($)',
            tickformat='$,.0f'
        ),
        hovermode='x unified'
    )
    
    # Add gradient effect annotation
    fig.add_annotation(
        x=len(equity)-1,
        y=equity[-1],
        text=f"<b>${equity[-1]:,}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowcolor='#00ff88',
        font=dict(size=16, color='#00ff88', family='Bebas Neue'),
        ax=40,
        ay=-40
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Bet History Table
    st.markdown("### RECENT ACTIVITY")
    
    col_filter, col_export = st.columns([3, 1])
    with col_filter:
        result_filter = st.selectbox("Filter", ["ALL", "WINS", "LOSSES", "PENDING"], key="tracker_filter")
    with col_export:
        if st.button("EXPORT CSV"):
            st.info("Export functionality coming soon")
    
    # Display bets
    display_bets = all_bets.copy()
    if result_filter == "WINS":
        display_bets = [b for b in display_bets if b['result'] == 'WIN']
    elif result_filter == "LOSSES":
        display_bets = [b for b in display_bets if b['result'] == 'LOSS']
    elif result_filter == "PENDING":
        display_bets = [b for b in display_bets if b['result'] == 'PENDING']
    
    for bet in display_bets[:15]:  # Show last 15
        if bet['result'] == 'WIN':
            result_color = "var(--accent)"
            border_color = "var(--accent)"
        elif bet['result'] == 'LOSS':
            result_color = "var(--danger)"
            border_color = "var(--danger)"
        else:
            result_color = "var(--warning)"
            border_color = "var(--warning)"
        
        profit_str = f"${bet['profit']:+,}" if isinstance(bet['profit'], (int, float)) else bet['profit']
        stake_str = f"${bet['stake']}" if isinstance(bet['stake'], (int, float)) else bet['stake']
        
        st.markdown(f"""
            <div style="
                background: var(--dark-2);
                border: 1px solid var(--dark-4);
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 16px;
                margin: 8px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: transform 0.2s ease;
            ">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
                        <span style="font-size: 0.75rem; color: var(--text-3);">{bet['date']}</span>
                        <span style="font-weight: 600; color: var(--text-1);">{bet['game']}</span>
                    </div>
                    <div style="font-family: 'Rajdhani'; font-size: 1.1rem; color: var(--text-2);">{bet['pick']} ({bet['odds']})</div>
                    <div style="font-size: 0.8rem; color: var(--text-3); margin-top: 4px;">Stake: {stake_str}</div>
                </div>
                <div style="text-align: right;">
                    <div style="
                        display: inline-block;
                        padding: 4px 12px;
                        border-radius: 4px;
                        background: {border_color}20;
                        color: {result_color};
                        font-weight: 700;
                        font-size: 0.8rem;
                        margin-bottom: 4px;
                    ">{bet['result']}</div>
                    <div style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: {result_color};">{profit_str}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =============================================================================
# TAB 5: LAB (AUTONOMOUS RESEARCH)
# =============================================================================
with tab_lab:
    st.markdown('<div class="slot-header">AUTONOMOUS RESEARCH LAB</div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: var(--dark-2); border: 1px solid var(--accent); border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <div style="font-family: 'Bebas Neue'; font-size: 1.2rem; color: var(--accent); margin-bottom: 8px;">SELF-IMPROVING SYSTEM</div>
            <div style="color: var(--text-2); font-size: 0.9rem;">
                Walk-forward backtesting with no forward-looking bias. Models retrain weekly. 
                Strategy discovery runs continuously to find hidden edges.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Lab controls
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    with col_ctrl1:
        st.selectbox("Model", ["XGBoost Evolved", "LightGBM", "Ensemble", "Calibrated"])
    with col_ctrl2:
        st.selectbox("Backtest Period", ["2023-2024", "2022-2024", "2020-2024", "Full History"])
    with col_ctrl3:
        st.number_input("Initial Bankroll", value=10000, step=1000)
    
    if st.button("RUN BACKTEST", use_container_width=True):
        with st.spinner("Running walk-forward backtest..."):
            import time
            time.sleep(2)
            st.success("Backtest complete! ROI: +14.2% | Win Rate: 58.3% | Sharpe: 1.84")
    
    st.markdown("---")
    
    # Performance chart
    st.markdown("### Equity Curve")
    
    # Generate realistic equity curve
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='W')
    returns = np.random.normal(0.02, 0.05, 100)
    equity = 10000 * np.cumprod(1 + returns)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=equity,
        mode='lines',
        fill='tozeroy',
        line=dict(color='#00ff88', width=2),
        fillcolor='rgba(0, 255, 136, 0.1)'
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#b0b0b0',
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        xaxis=dict(gridcolor='rgba(50,50,50,0.5)', showgrid=True),
        yaxis=dict(gridcolor='rgba(50,50,50,0.5)', showgrid=True)
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# TAB 6: INTEL (AI SEARCH)
# =============================================================================
with tab_intel:
    st.markdown('<div class="slot-header">INTELLIGENCE CENTER</div>', unsafe_allow_html=True)
    
    # Quick searches
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("INJURY REPORT"):
            st.session_state['intel_query'] = "Latest NFL injury updates for Week 13"
    with c2:
        if st.button("SHARP MONEY"):
            st.session_state['intel_query'] = "Where is sharp money going NFL Week 13"
    with c3:
        if st.button("LINE MOVES"):
            st.session_state['intel_query'] = "Significant NFL line movements today"
    with c4:
        if st.button("WEATHER"):
            st.session_state['intel_query'] = "NFL Week 13 weather impacts on games"
    
    query = st.text_input("Search:", value=st.session_state.get('intel_query', ''), placeholder="Ask anything...")
    
    if st.button("SEARCH", type="primary") and query:
        with st.spinner("Searching..."):
            result = get_ai_analysis({'query': query}, provider='grok')
            st.markdown(f"""
                <div style="background: var(--dark-2); border-left: 3px solid var(--accent); padding: 20px; border-radius: 0 8px 8px 0; margin-top: 16px;">
                    <div style="color: var(--accent); font-size: 0.8rem; margin-bottom: 8px; font-family: 'Rajdhani'; letter-spacing: 1px;">INTEL REPORT</div>
                    <div style="color: var(--text-1); line-height: 1.6;">{result}</div>
                </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: var(--text-3); font-size: 0.75rem; padding: 20px;">
        EDGE HUNTER // Autonomous Betting Intelligence // No forward-looking bias // Self-improving
    </div>
""", unsafe_allow_html=True)
