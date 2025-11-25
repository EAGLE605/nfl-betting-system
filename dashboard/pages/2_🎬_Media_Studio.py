import streamlit as st
import pandas as pd
import time

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# -----------------------------------------------------------------------------
# 1. API CONFIGURATION
# -----------------------------------------------------------------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")

if GENAI_AVAILABLE:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except:
        pass

# -----------------------------------------------------------------------------
# 2. PAGE SETUP & CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Media Studio", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        .stApp { background-color: #0b0e11; color: white; font-family: 'Inter'; }
        
        /* HYPE CARD STYLE */
        .hype-container {
            border: 2px solid #a855f7; /* Purple Neon */
            border-radius: 15px;
            padding: 20px;
            background: linear-gradient(145deg, #1e1b4b, #0b0e11);
            text-align: center;
            box-shadow: 0 0 30px rgba(168, 85, 247, 0.3);
            margin-bottom: 20px;
        }
        .hype-title { font-size: 2rem; font-weight: 900; color: #fff; text-transform: uppercase; }
        .hype-tag { color: #4ade80; font-weight: bold; font-size: 1.2rem; }
        
        /* BUTTONS */
        div.stButton > button {
            background: linear-gradient(90deg, #a855f7, #6366f1);
            border: none;
            color: white;
            font-weight: bold;
        }
        div.stButton > button:hover {
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. GENERATION LOGIC
# -----------------------------------------------------------------------------

def generate_hype_card(game_data):
    """
    Uses 'Nano Banana Pro' (Gemini 3 Image) to generate a betting card.
    """
    prompt = f"""
    A cinematic, high-stakes sports betting graphic for the NFL game: {game_data['Home Team']} vs {game_data['Away Team']}.
    
    VISUALS:
    - Split screen composition: {game_data['Home Team']} star player on left (in home colors), {game_data['Away Team']} star player on right (in away colors).
    - Background: A futuristic stadium tunnel with neon lighting (Team colors).
    - Style: 8k resolution, Unreal Engine 5 render, hyper-realistic, dramatic lighting.

    TEXT OVERLAY (MUST BE PERFECT SPELLING):
    - Center big text: "{game_data['Prediction'].upper()}"
    - Subtext glowing green: "CONFIDENCE {game_data['Confidence']}%"
    - Bottom text: "AI LOCK OF THE WEEK"
    
    Use the Nano Banana Pro engine for flawless text rendering.
    """

    if not GENAI_AVAILABLE:
        st.error("google-generativeai not installed. Run: pip install google-generativeai")
        return None

    try:
        # Model options: 'gemini-3-pro-image-preview', 'imagen-3.0-generate-001'
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter="block_only_high",
        )
        return response.images[0]
    except Exception as e:
        st.error(f"Image Gen Failed: {e}")
        return None


def generate_notebook_video(game_data):
    """
    Simulates calling the NotebookLM 'Video Overview' API.
    """
    # NOTE: This endpoint is hypothetical - simulating for demo
    time.sleep(3)  # Simulate processing
    return True


# -----------------------------------------------------------------------------
# 4. LAYOUT
# -----------------------------------------------------------------------------

st.title("🎬 Media Studio")
st.markdown("Generate social-ready betting cards and AI analysis videos.")

# Mock Data for Demo
df = pd.DataFrame([
    {"Home Team": "Lions", "Away Team": "Bears", "Prediction": "Lions", "Confidence": 88.5, "Odds": "-140"},
    {"Home Team": "Chiefs", "Away Team": "Bills", "Prediction": "Chiefs", "Confidence": 72.3, "Odds": "-155"},
    {"Home Team": "Eagles", "Away Team": "Cowboys", "Prediction": "Eagles", "Confidence": 65.8, "Odds": "-120"},
])

col1, col2 = st.columns([1, 2])

with col1:
    st.info("Select a game to generate content")
    selected_game_index = st.selectbox(
        "Choose Game", 
        df.index, 
        format_func=lambda x: f"{df.iloc[x]['Home Team']} vs {df.iloc[x]['Away Team']}"
    )
    game_data = df.iloc[selected_game_index]
    
    # Show selected game details
    st.markdown("#### Selected Game")
    st.markdown(f"""
        <div style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #a855f7;">
            <div style="font-size: 1.2rem; font-weight: bold;">{game_data['Home Team']} vs {game_data['Away Team']}</div>
            <div style="color: #4ade80; font-weight: bold;">AI Pick: {game_data['Prediction']}</div>
            <div style="color: #94a3b8;">Confidence: {game_data['Confidence']}%</div>
            <div style="color: #94a3b8;">Odds: {game_data['Odds']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # IMAGE GENERATION BUTTON
    if st.button("🎨 Generate Hype Card (Nano Banana Pro)", type="primary", use_container_width=True):
        with st.spinner("Rendering 4K graphics with Gemini 3..."):
            img = generate_hype_card(game_data)
            if img:
                st.session_state['last_image'] = img
                st.success("Card Generated!")
    
    st.markdown("")
    
    # VIDEO GENERATION BUTTON
    if st.button("🎥 Generate NotebookLM Deep Dive", use_container_width=True):
        with st.spinner("AI Hosts are discussing the matchup..."):
            res = generate_notebook_video(game_data)
            st.session_state['video_ready'] = True
            st.success("Video Analysis Ready!")

with col2:
    # DISPLAY AREA
    st.markdown('<div class="hype-container"><div class="hype-title">Content Preview</div></div>', unsafe_allow_html=True)
    
    if 'last_image' in st.session_state:
        st.image(st.session_state['last_image'], caption="Generated by Nano Banana Pro", use_container_width=True)
        st.download_button("📥 Download Card", data="fake_bytes", file_name="bet_card.png", use_container_width=True)
        
    if 'video_ready' in st.session_state:
        st.markdown("### 🎧 AI Analysis Video")
        # In a real app, this would be the URL from the API
        st.video("https://www.w3schools.com/html/mov_bbb.mp4", format="video/mp4")
        st.caption("Hosts: 'Deep Dive' Audio + Nano Banana Visuals")
    
    if 'last_image' not in st.session_state and 'video_ready' not in st.session_state:
        st.markdown("""
            <div style="text-align: center; padding: 60px 20px; color: #64748b;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🎨</div>
                <div style="font-size: 1.2rem;">Select a game and click Generate</div>
                <div style="font-size: 0.9rem; margin-top: 10px;">Your AI-generated content will appear here</div>
            </div>
        """, unsafe_allow_html=True)

