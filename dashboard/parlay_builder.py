import streamlit as st
import pandas as pd
import uuid

# -----------------------------------------------------------------------------
# 1. SETUP & CSS (The "Slate" Theme)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Parlay Builder", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
        /* DARK SLATE THEME */
        .stApp { background-color: #0f172a; color: #f8fafc; }
        
        /* CARD STYLING (The Betting Lines) */
        .bet-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            transition: transform 0.2s;
        }
        .bet-card:hover { border-color: #38bdf8; }
        
        /* THE BET SLIP (Right Sidebar) */
        .slip-container {
            background-color: #1e293b;
            border: 1px solid #38bdf8; /* Blue border for active slip */
            border-radius: 12px;
            padding: 20px;
            position: sticky;
            top: 2rem;
        }
        
        /* ODDS BUTTONS */
        div.stButton > button {
            background-color: #334155;
            color: white;
            border: none;
            width: 100%;
            font-weight: bold;
            border-radius: 4px;
        }
        div.stButton > button:hover {
            background-color: #38bdf8; /* Light Blue hover */
            color: #0f172a;
        }
        
        /* PAYOUT TEXT */
        .payout-text {
            font-size: 2rem;
            font-weight: 900;
            color: #4ade80; /* Neon Green */
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT (The "Shopping Cart")
# -----------------------------------------------------------------------------
if 'slip' not in st.session_state:
    st.session_state.slip = []


def add_to_slip(player, prop, line, odds, game):
    # Unique ID to allow deleting specific legs later
    bet_id = str(uuid.uuid4())
    st.session_state.slip.append({
        "id": bet_id,
        "player": player,
        "prop": prop,
        "line": line,
        "odds": odds,
        "game": game
    })


def remove_from_slip(bet_id):
    st.session_state.slip = [bet for bet in st.session_state.slip if bet['id'] != bet_id]


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
        dec = american_to_decimal(bet['odds'])
        total_multiplier *= dec
        
    final_odds = decimal_to_american(total_multiplier)
    payout = wager * total_multiplier
    
    # Formatting
    odds_str = f"+{final_odds}" if final_odds > 0 else str(final_odds)
    return payout, total_multiplier, odds_str


# -----------------------------------------------------------------------------
# 4. MOCK DATA (The Betting Market)
# -----------------------------------------------------------------------------
# In a real app, this comes from your 'main.py' or API
props_db = [
    {"id": 1, "game": "DET @ DAL", "player": "Jahmyr Gibbs", "prop": "Anytime TD", "line": "", "odds": -120},
    {"id": 2, "game": "DET @ DAL", "player": "Amon-Ra St. Brown", "prop": "Receiving Yds", "line": "Over 82.5", "odds": -115},
    {"id": 3, "game": "KC @ BUF", "player": "Josh Allen", "prop": "Passing TDs", "line": "Over 1.5", "odds": -140},
    {"id": 4, "game": "KC @ BUF", "player": "Travis Kelce", "prop": "Receptions", "line": "Over 6.5", "odds": +100},
    {"id": 5, "game": "PHI @ NYG", "player": "Saquon Barkley", "prop": "Rushing Yds", "line": "Over 75.5", "odds": -110},
    {"id": 6, "game": "PHI @ NYG", "player": "Jalen Hurts", "prop": "Anytime TD", "line": "", "odds": +110},
]

# -----------------------------------------------------------------------------
# 5. LAYOUT
# -----------------------------------------------------------------------------

st.title("🧩 Parlay Architect")
st.markdown("Build +EV Parlays based on correlated outcomes.")

col_market, col_slip = st.columns([2, 1])

# --- LEFT COLUMN: THE MARKET ---
with col_market:
    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("League", ["NFL", "NBA", "NHL"])
    with c2:
        st.selectbox("Market", ["Player Props", "Game Lines", "Touchdowns"])
    with c3:
        st.text_input("Search", placeholder="e.g. Chiefs")
    
    st.markdown("### Available Props")
    
    # Loop through data and create "Cards"
    for prop in props_db:
        # Visual Card
        with st.container():
            st.markdown(f"""
                <div class="bet-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="color:#94a3b8; font-size:0.8rem;">{prop['game']}</div>
                            <div style="font-weight:bold; font-size:1.1rem; color:#f8fafc;">{prop['player']}</div>
                            <div style="color:#38bdf8;">{prop['prop']} {prop['line']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.2rem; font-weight:900; color:#4ade80;">{prop['odds'] if prop['odds'] > 0 else prop['odds']}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # The "Add" Button (Streamlit limitation: buttons must be outside HTML block)
            # We use a unique key so every button works independently
            btn_col1, btn_col2 = st.columns([4, 1])
            with btn_col2:
                if st.button("ADD +", key=f"add_{prop['id']}"):
                    add_to_slip(prop['player'], prop['prop'], prop['line'], prop['odds'], prop['game'])
                    st.rerun()

# --- RIGHT COLUMN: THE BET SLIP ---
with col_slip:
    st.markdown("### 🎫 Your Slip")
    
    # Container styling
    with st.container():
        st.markdown('<div class="slip-container">', unsafe_allow_html=True)
        
        if not st.session_state.slip:
            st.info("Slip is empty. Add legs from the left!")
        else:
            # 1. List Items
            for leg in st.session_state.slip:
                c_info, c_del = st.columns([4, 1])
                with c_info:
                    st.markdown(f"**{leg['player']}**")
                    st.caption(f"{leg['prop']} {leg['line']} ({leg['odds']})")
                with c_del:
                    if st.button("✖", key=f"del_{leg['id']}"):
                        remove_from_slip(leg['id'])
                        st.rerun()
                st.divider()
            
            # 2. Wager Input
            wager = st.number_input("Wager ($)", min_value=1, value=50, step=10)
            
            # 3. Calculations
            potential_payout, multiplier, final_odds = calculate_parlay(st.session_state.slip, wager)
            
            st.markdown("---")
            
            # Summary Stats
            r1, r2 = st.columns(2)
            with r1:
                st.metric("Total Odds", final_odds)
            with r2:
                st.metric("Legs", len(st.session_state.slip))
            
            # BIG PAYOUT DISPLAY
            st.markdown("##### Potential Payout")
            st.markdown(f'<div class="payout-text">${potential_payout:,.2f}</div>', unsafe_allow_html=True)
            
            # Action Button
            st.button("🚀 PLACE BET NOW", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
