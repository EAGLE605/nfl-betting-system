import os
import time

import pandas as pd
import streamlit as st

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
    genai = None

# -----------------------------------------------------------------------------
# 1. PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Media Studio", page_icon="⚡", layout="wide")

# -----------------------------------------------------------------------------
# 2. API CONFIGURATION
# -----------------------------------------------------------------------------
def get_secret(key):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, "")

GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
XAI_API_KEY = get_secret("XAI_API_KEY")

if GENAI_AVAILABLE and GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 3. TEAM DATA
# -----------------------------------------------------------------------------
TEAM_LOGOS = {
    "Lions": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png",
    "Bears": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png",
    "Chiefs": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
    "Bills": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
    "Eagles": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",
    "Cowboys": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "49ers": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
    "Seahawks": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
    "Packers": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
    "Vikings": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png",
    "Ravens": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png",
    "Bengals": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png",
    "Browns": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png",
    "Steelers": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png",
    "Dolphins": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png",
    "Patriots": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
    "Jets": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
    "Raiders": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png",
    "Chargers": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png",
    "Broncos": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png",
    "Texans": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png",
    "Colts": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png",
    "Titans": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png",
    "Jaguars": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png",
    "Saints": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png",
    "Falcons": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png",
    "Panthers": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png",
    "Buccaneers": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png",
    "Cardinals": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png",
    "Rams": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png",
    "Giants": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
    "Commanders": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png",
    "Over": "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png",
    "Under": "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png",
}

TEAM_COLORS = {
    "Lions": ("#0076B6", "#B0B7BC"),
    "Bears": ("#0B162A", "#C83803"),
    "Chiefs": ("#E31837", "#FFB81C"),
    "Bills": ("#00338D", "#C60C30"),
    "Eagles": ("#004C54", "#A5ACAF"),
    "Cowboys": ("#003594", "#869397"),
    "49ers": ("#AA0000", "#B3995D"),
    "Seahawks": ("#002244", "#69BE28"),
    "Packers": ("#203731", "#FFB612"),
    "Vikings": ("#4F2683", "#FFC62F"),
    "Ravens": ("#241773", "#9E7C0C"),
    "Bengals": ("#FB4F14", "#000000"),
    "Over": ("#22c55e", "#16a34a"),
    "Under": ("#ef4444", "#dc2626"),
}

# -----------------------------------------------------------------------------
# 4. CSS STYLING
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, .stApp { background-color: #0a0f1a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        #MainMenu, footer, header {visibility: hidden;}
        .stButton > button { background: #3b82f6; border: none; color: white; font-weight: 600; border-radius: 8px; }
        .stButton > button:hover { background: #2563eb; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. AI ANALYSIS FUNCTION (MULTI-PROVIDER)
# -----------------------------------------------------------------------------
def generate_ai_analysis(game_data, provider="grok"):
    """Use Grok, GPT, Claude, or Gemini to generate betting analysis."""
    prompt = f"""You are a sharp sports betting analyst. Give a confident 2-3 sentence analysis for this NFL bet:

Game: {game_data['Away']} @ {game_data['Home']}
BET: {game_data['Pick']} {game_data['Line']} ({game_data['Type']})
Odds: {game_data['Odds']}
Confidence: {game_data['Confidence']}%

Explain WHY this bet wins. Be specific about matchups or trends. Use betting terminology. Keep it punchy."""

    # GROK (xAI) - OpenAI compatible
    if provider == "grok" and OPENAI_AVAILABLE and XAI_API_KEY:
        try:
            client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)
            response = client.chat.completions.create(
                model="grok-3-mini",
                messages=[
                    {"role": "system", "content": "You are a sharp sports betting analyst. Be concise and confident."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content, "Grok-3"
        except Exception as e:
            pass

    # GPT
    if provider == "gpt" and OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return response.choices[0].message.content, "GPT-4o"
        except Exception as e:
            pass

    # Claude
    if provider == "claude" and ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text, "Claude Haiku"
        except Exception as e:
            pass
    
    # Gemini
    if provider == "gemini" and GENAI_AVAILABLE and GOOGLE_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text, "Gemini Pro"
        except Exception as e:
            pass
    
    # Fallback
    pick = game_data['Pick']
    line = game_data['Line'] if game_data['Line'] else 'ML'
    return f"Sharp money is backing {pick} {line} at {game_data['Odds']}. The model shows {game_data['Confidence']}% confidence based on recent performance trends and matchup advantages.", "Fallback"


def generate_hype_card_html(game_data):
    """Generate a stylized HTML hype card with logo and bet details."""
    pick_team = game_data['Pick']
    logo_url = TEAM_LOGOS.get(pick_team, "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png")
    colors = TEAM_COLORS.get(pick_team, ("#3b82f6", "#1e40af"))
    primary, secondary = colors
    
    bet_type = game_data['Type']
    line = game_data['Line']
    
    if bet_type == "ML":
        bet_display = f"{pick_team} ML"
        bet_label = "MONEYLINE"
    elif bet_type == "O/U":
        bet_display = f"{game_data['Pick']} {line}"
        bet_label = "TOTAL"
    else:
        bet_display = f"{pick_team} {line}"
        bet_label = "SPREAD"
    
    return f"""
    <div style="
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
        border-radius: 16px;
        padding: 0;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        border: 1px solid #334155;
        margin: 10px 0;
        overflow: hidden;
    ">
        <div style="
            background: linear-gradient(90deg, {primary}, {secondary});
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <span style="font-size: 0.8rem; font-weight: 700; color: white; letter-spacing: 1px;">NFL {bet_label}</span>
            <span style="font-size: 0.8rem; font-weight: 600; color: rgba(255,255,255,0.8);">GAMELOCK AI</span>
        </div>
        
        <div style="padding: 30px; text-align: center;">
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 15px;">
                {game_data['Away']} @ {game_data['Home']}
            </div>
            
            <img src="{logo_url}" style="
                width: 120px; 
                height: 120px; 
                margin: 10px auto;
                filter: drop-shadow(0 0 20px {primary}44);
            ">
            
            <div style="
                font-size: 2.5rem; 
                font-weight: 800; 
                color: #fff; 
                margin: 20px 0 8px 0;
            ">
                {bet_display}
            </div>
            
            <div style="
                font-size: 1.6rem;
                font-weight: 700;
                color: #22c55e;
                margin-bottom: 20px;
            ">
                {game_data['Odds']}
            </div>
            
            <div style="
                display: inline-block;
                background: #22c55e;
                padding: 10px 24px;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 700;
                color: #fff;
            ">
                {game_data['Confidence']}% CONFIDENCE
            </div>
        </div>
    </div>
    """


# -----------------------------------------------------------------------------
# 6. LAYOUT
# -----------------------------------------------------------------------------

# Header with AI status
ai_list = []
if OPENAI_AVAILABLE and XAI_API_KEY: ai_list.append("Grok")
if OPENAI_AVAILABLE and OPENAI_API_KEY: ai_list.append("GPT")
if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY: ai_list.append("Claude")
if GENAI_AVAILABLE and GOOGLE_API_KEY: ai_list.append("Gemini")
ai_badge = f"<span style='background:#6366f1;color:#fff;padding:4px 10px;border-radius:15px;font-size:0.7rem;font-weight:600;margin-left:10px;'>{' • '.join(ai_list) if ai_list else 'No AI'}</span>"

st.markdown(f"""
    <div style="margin-bottom: 25px;">
        <span style="font-size: 1.5rem; font-weight: 700; color: #fff;">Media Studio</span>
        <span style="color: #64748b; margin-left: 10px;">Generate shareable bet cards</span>
        {ai_badge}
    </div>
""", unsafe_allow_html=True)

# BETTING DATA
df = pd.DataFrame([
    {"Away": "Bears", "Home": "Lions", "Pick": "Lions", "Type": "Spread", "Line": "-6.5", "Odds": "-110", "Confidence": 78.2},
    {"Away": "Bills", "Home": "Chiefs", "Pick": "Chiefs", "Type": "ML", "Line": "", "Odds": "-145", "Confidence": 71.5},
    {"Away": "Cowboys", "Home": "Eagles", "Pick": "Cowboys", "Type": "Spread", "Line": "+4.5", "Odds": "-105", "Confidence": 62.8},
    {"Away": "Seahawks", "Home": "49ers", "Pick": "49ers", "Type": "ML", "Line": "", "Odds": "-175", "Confidence": 75.3},
    {"Away": "Packers", "Home": "Vikings", "Pick": "Under", "Type": "O/U", "Line": "47.5", "Odds": "-110", "Confidence": 58.9},
])

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### Select Bet")
    
    selected_idx = st.selectbox(
        "Choose a pick",
        df.index,
        format_func=lambda x: f"{df.iloc[x]['Pick']} {df.iloc[x]['Line']} ({df.iloc[x]['Type']})" if df.iloc[x]['Line'] else f"{df.iloc[x]['Pick']} ML",
        label_visibility="collapsed"
    )
    game_data = df.iloc[selected_idx]
    
    # Bet Details
    st.markdown(f"""
        <div style="
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
            margin: 15px 0;
        ">
            <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 6px;">SELECTED BET</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #fff;">
                {game_data['Pick']} {game_data['Line'] if game_data['Line'] else 'ML'}
            </div>
            <div style="color: #94a3b8; margin-top: 6px;">
                {game_data['Away']} @ {game_data['Home']}
            </div>
            <div style="display: flex; gap: 20px; margin-top: 12px;">
                <div>
                    <span style="color: #64748b; font-size: 0.75rem;">ODDS</span><br>
                    <span style="color: #22c55e; font-weight: 600;">{game_data['Odds']}</span>
                </div>
                <div>
                    <span style="color: #64748b; font-size: 0.75rem;">CONF</span><br>
                    <span style="color: #f59e0b; font-weight: 600;">{game_data['Confidence']}%</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # AI Provider Selector
    providers = []
    if OPENAI_AVAILABLE and XAI_API_KEY: providers.append("Grok")
    if OPENAI_AVAILABLE and OPENAI_API_KEY: providers.append("GPT")
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY: providers.append("Claude")
    if GENAI_AVAILABLE and GOOGLE_API_KEY: providers.append("Gemini")
    if not providers: providers = ["Fallback"]
    
    ai_provider = st.selectbox("AI Provider", providers, label_visibility="collapsed")
    
    # AI Analysis Button
    if st.button("Generate AI Analysis", use_container_width=True, type="primary"):
        with st.spinner(f"Analyzing with {ai_provider}..."):
            analysis_text, provider_used = generate_ai_analysis(game_data.to_dict(), provider=ai_provider.lower())
            st.session_state['analysis'] = analysis_text
            st.session_state['provider_used'] = provider_used
            st.rerun()

with col2:
    # Auto-generate hype card on selection
    st.markdown(generate_hype_card_html(game_data.to_dict()), unsafe_allow_html=True)
    
    # Show AI Analysis
    if 'analysis' in st.session_state:
        provider_used = st.session_state.get('provider_used', 'AI')
        st.markdown(f"""
            <div style="
                background: #1e293b;
                border-left: 4px solid #6366f1;
                padding: 16px;
                border-radius: 8px;
                margin-top: 15px;
            ">
                <div style="color: #6366f1; font-weight: 600; font-size: 0.85rem; margin-bottom: 8px;">AI ANALYSIS • {provider_used}</div>
                <div style="color: #e2e8f0; line-height: 1.6;">{st.session_state['analysis']}</div>
            </div>
        """, unsafe_allow_html=True)
