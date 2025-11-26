import uuid

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. SETUP & CSS (OddsJam Dark Theme)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Parlay Builder", page_icon="🏈", layout="wide")

# NFL Team logos (using ESPN CDN)
TEAM_LOGOS = {
    "Lions": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png",
    "Bears": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png",
    "Chiefs": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
    "Bills": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
    "Eagles": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",
    "Giants": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
    "Cowboys": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "Jaguars": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png",
    "Titans": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png",
    "Cardinals": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png",
    "Buccaneers": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png",
    "Bengals": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png",
    "Ravens": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png",
    "49ers": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
    "Seahawks": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
    "Dolphins": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png",
    "Patriots": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
    "Jets": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
    "Packers": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
    "Vikings": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png",
    "Broncos": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png",
    "Raiders": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png",
    "Chargers": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png",
    "Steelers": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png",
    "Browns": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png",
    "Colts": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png",
    "Texans": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png",
    "Falcons": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png",
    "Saints": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png",
    "Panthers": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png",
    "Commanders": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png",
    "Rams": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png",
}

st.markdown(
    """
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        /* DARK NAVY THEME (OddsJam Style) */
        .stApp { 
            background-color: #0d1421; 
            color: #e2e8f0; 
            font-family: 'Inter', sans-serif;
        }
        
        /* HIDE STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* MAIN CONTAINER */
        .block-container {
            padding-top: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        
        /* BET SLIP CARD */
        .bet-slip-card {
            background-color: #131c2e;
            border: 1px solid #1e2d45;
            border-radius: 12px;
            padding: 0;
            overflow: hidden;
        }
        
        /* SLIP HEADER */
        .slip-header {
            background-color: #131c2e;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e2d45;
        }
        .slip-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .slip-odds {
            font-size: 1.1rem;
            font-weight: 700;
            color: #22d3ee;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* BET LEG ITEM */
        .bet-leg {
            background-color: #131c2e;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            border-bottom: 1px solid #1e2d45;
        }
        .bet-leg:last-child {
            border-bottom: none;
        }
        .team-logo {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            object-fit: contain;
            background: #1a2744;
            padding: 4px;
        }
        .bet-info {
            flex: 1;
        }
        .bet-title {
            font-size: 1rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 2px;
        }
        .bet-prop {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 2px;
        }
        .bet-matchup {
            font-size: 0.8rem;
            color: #475569;
        }
        .bet-odds {
            font-size: 1.1rem;
            font-weight: 700;
            color: #22d3ee;
        }
        
        /* YOUR BET SECTION */
        .your-bet-card {
            background-color: #131c2e;
            border: 1px solid #1e2d45;
            border-radius: 12px;
            padding: 20px;
        }
        .your-bet-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 16px;
        }
        .input-group {
            margin-bottom: 16px;
        }
        .input-label {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 6px;
        }
        .input-wrapper {
            background-color: #1a2744;
            border: 1px solid #1e2d45;
            border-radius: 8px;
            display: flex;
            align-items: center;
            padding: 0 12px;
        }
        .input-prefix {
            color: #64748b;
            font-weight: 500;
        }
        
        /* PROFIT DISPLAY */
        .profit-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #4ade80;
        }
        
        /* PROP CARD (Market Browser) */
        .prop-card {
            background-color: #131c2e;
            border: 1px solid #1e2d45;
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: border-color 0.2s;
        }
        .prop-card:hover {
            border-color: #22d3ee;
        }
        
        /* BUTTONS */
        div.stButton > button {
            background-color: #1e2d45;
            color: #e2e8f0;
            border: 1px solid #2d3f5a;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #22d3ee;
            color: #0d1421;
            border-color: #22d3ee;
        }
        
        /* PRIMARY BUTTON */
        .stButton > button[kind="primary"] {
            background-color: #1e2d45;
            border: 1px solid #2d3f5a;
        }
        
        /* PAGE TITLE */
        .page-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }
        .page-subtitle {
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 24px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT (Shopping Cart)
# -----------------------------------------------------------------------------
if "slip" not in st.session_state:
    st.session_state.slip = []


def add_to_slip(player, prop, line, odds, game, team):
    bet_id = str(uuid.uuid4())
    st.session_state.slip.append(
        {
            "id": bet_id,
            "player": player,
            "prop": prop,
            "line": line,
            "odds": odds,
            "game": game,
            "team": team,
        }
    )


def remove_from_slip(bet_id):
    st.session_state.slip = [
        bet for bet in st.session_state.slip if bet["id"] != bet_id
    ]


def clear_slip():
    st.session_state.slip = []


# -----------------------------------------------------------------------------
# 3. MATH (Parlay Calculator)
# -----------------------------------------------------------------------------
def american_to_decimal(american_odds):
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def decimal_to_american(decimal_odds):
    if decimal_odds >= 2:
        return round((decimal_odds - 1) * 100)
    else:
        return round(-100 / (decimal_odds - 1))


def calculate_parlay(slip, wager):
    if not slip:
        return 0, 0, "+0"

    total_multiplier = 1.0
    for bet in slip:
        dec = american_to_decimal(bet["odds"])
        total_multiplier *= dec

    final_odds = decimal_to_american(total_multiplier)
    payout = wager * total_multiplier
    profit = payout - wager

    odds_str = f"+{final_odds}" if final_odds > 0 else str(final_odds)
    return profit, total_multiplier, odds_str


# -----------------------------------------------------------------------------
# 4. LIVE ODDS DATA (From The Odds API)
# -----------------------------------------------------------------------------

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_live_odds():
    """Fetch real NFL odds from The Odds API."""
    try:
        from agents.api_integrations import TheOddsAPI

        api = TheOddsAPI()
        if not api.api_key:
            st.sidebar.warning("⚠️ ODDS_API_KEY not set - showing cached data")
            return []

        games = api.get_nfl_odds(markets="h2h,spreads,totals")

        props_data = []
        prop_id = 1

        for game in games:
            home_team = game.get("home_team", "Unknown")
            away_team = game.get("away_team", "Unknown")
            game_name = f"{away_team} @ {home_team}"

            # Get short team names
            home_short = home_team.split()[-1]
            away_short = away_team.split()[-1]

            for bookmaker in game.get("bookmakers", []):
                if bookmaker.get("key") in ["fanduel", "draftkings", "betmgm"]:
                    for market in bookmaker.get("markets", []):
                        market_key = market.get("key")

                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name", "")
                            price = outcome.get("price", 0)
                            point = outcome.get("point")

                            # Build prop description
                            if market_key == "h2h":
                                prop = "Moneyline"
                                player = name
                                team = name.split()[-1] if name else "Unknown"
                            elif market_key == "spreads":
                                point_str = f"+{point}" if point > 0 else str(point)
                                prop = f"Spread {point_str}"
                                player = name
                                team = name.split()[-1] if name else "Unknown"
                            elif market_key == "totals":
                                prop = f"Total {name}"
                                player = f"{name} {point}" if point else name
                                team = home_short
                            else:
                                continue

                            props_data.append(
                                {
                                    "id": prop_id,
                                    "game": game_name,
                                    "team": team,
                                    "player": player,
                                    "prop": prop,
                                    "line": str(point) if point else "",
                                    "odds": int(price) if price else 0,
                                    "bookmaker": bookmaker.get("title", "Unknown"),
                                }
                            )
                            prop_id += 1
                    break  # Only use first matching bookmaker

        return props_data

    except Exception as e:
        st.sidebar.error(f"Error fetching odds: {e}")
        return []


def get_props_db():
    """Get props database - live if available, otherwise empty."""
    props = fetch_live_odds()

    if not props:
        # Return empty list with message
        st.info(
            "📡 No live odds available. Set ODDS_API_KEY environment variable to enable live data."
        )
        return []

    return props


# Fetch live data
props_db = get_props_db()

# -----------------------------------------------------------------------------
# 5. LAYOUT
# -----------------------------------------------------------------------------

st.markdown(
    '<div class="page-title">Best NFL Parlay Bets Today</div>', unsafe_allow_html=True
)

# Dynamic subtitle based on slip
if st.session_state.slip:
    slip_desc = " and ".join(
        [
            f"{leg['player']} {leg['prop']} ({'+' if leg['odds'] > 0 else ''}{leg['odds']})"
            for leg in st.session_state.slip[:3]
        ]
    )
    _, _, total_odds = calculate_parlay(st.session_state.slip, 100)
    st.markdown(
        f'<div class="page-subtitle">{slip_desc} for a return of <b>{total_odds}</b></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="page-subtitle">Build your parlay by selecting props from the market below</div>',
        unsafe_allow_html=True,
    )

col_slip, col_bet = st.columns([2, 1])

# --- LEFT: BET SLIP ---
with col_slip:
    if st.session_state.slip:
        _, _, total_odds = calculate_parlay(st.session_state.slip, 100)

        # Slip Header
        st.markdown(
            f"""
            <div class="bet-slip-card">
                <div class="slip-header">
                    <div class="slip-title">
                        🎫 {len(st.session_state.slip)}-Leg Bet Slip
                    </div>
                    <div class="slip-odds">
                        {total_odds} 🛡️
                    </div>
                </div>
        """,
            unsafe_allow_html=True,
        )

        # Slip Legs
        for leg in st.session_state.slip:
            logo_url = TEAM_LOGOS.get(
                leg["team"], "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png"
            )
            odds_display = f"+{leg['odds']}" if leg["odds"] > 0 else str(leg["odds"])

            st.markdown(
                f"""
                <div class="bet-leg">
                    <img src="{logo_url}" class="team-logo" alt="{leg['team']}">
                    <div class="bet-info">
                        <div class="bet-title">{leg['player']}</div>
                        <div class="bet-prop">{leg['prop']}</div>
                        <div class="bet-matchup">{leg['game']}</div>
                    </div>
                    <div class="bet-odds">{odds_display}</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Clear button
        if st.button("🗑️ Clear Slip", use_container_width=True):
            clear_slip()
            st.rerun()
    else:
        st.markdown(
            """
            <div class="bet-slip-card" style="padding: 40px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 12px;">🎫</div>
                <div style="color: #64748b;">Your bet slip is empty</div>
                <div style="color: #475569; font-size: 0.85rem; margin-top: 4px;">Add props from below to build your parlay</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

# --- RIGHT: YOUR BET ---
with col_bet:
    st.markdown('<div class="your-bet-card">', unsafe_allow_html=True)
    st.markdown('<div class="your-bet-title">Your bet</div>', unsafe_allow_html=True)

    # Wager Input
    st.markdown('<div class="input-label">Wager</div>', unsafe_allow_html=True)
    wager = st.number_input(
        "Wager", min_value=1, value=100, step=10, label_visibility="collapsed"
    )

    # Calculate profit
    profit, multiplier, final_odds = calculate_parlay(st.session_state.slip, wager)

    # Profit Display
    st.markdown(
        '<div class="input-label" style="margin-top: 16px;">Profit</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="input-wrapper" style="padding: 12px;">
            <span class="input-prefix">$</span>
            <span class="profit-value" style="margin-left: 8px;">{profit:,.2f}</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

    # Add to Bet Tracker Button
    if st.button(
        "Add to Bet Tracker",
        type="primary",
        use_container_width=True,
        disabled=len(st.session_state.slip) == 0,
    ):
        st.success("Added to Bet Tracker!")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# --- MARKET BROWSER ---
st.markdown("### 📋 Available Props")

# Filters
c1, c2, c3 = st.columns(3)
with c1:
    st.selectbox("League", ["NFL", "NBA", "NHL", "MLB"], key="league_filter")
with c2:
    st.selectbox(
        "Market",
        ["All Props", "Player Props", "Game Lines", "Touchdowns", "Quarters"],
        key="market_filter",
    )
with c3:
    st.text_input("Search", placeholder="e.g. Ja'Marr Chase", key="search_filter")

# Props Grid
for prop in props_db:
    logo_url = TEAM_LOGOS.get(
        prop["team"], "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png"
    )
    odds_display = f"+{prop['odds']}" if prop["odds"] > 0 else str(prop["odds"])

    col_card, col_btn = st.columns([5, 1])

    with col_card:
        st.markdown(
            f"""
            <div class="prop-card">
                <img src="{logo_url}" style="width: 44px; height: 44px; border-radius: 6px; object-fit: contain; background: #1a2744; padding: 4px;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #fff;">{prop['player']}</div>
                    <div style="font-size: 0.85rem; color: #64748b;">{prop['prop']}</div>
                    <div style="font-size: 0.8rem; color: #475569;">{prop['game']}</div>
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #22d3ee;">{odds_display}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col_btn:
        # Check if already in slip
        already_added = any(
            leg["id"] == str(prop["id"])
            or (leg["player"] == prop["player"] and leg["prop"] == prop["prop"])
            for leg in st.session_state.slip
        )

        if already_added:
            st.button("✓", key=f"add_{prop['id']}", disabled=True)
        else:
            if st.button("ADD", key=f"add_{prop['id']}"):
                add_to_slip(
                    prop["player"],
                    prop["prop"],
                    prop["line"],
                    prop["odds"],
                    prop["game"],
                    prop["team"],
                )
                st.rerun()
