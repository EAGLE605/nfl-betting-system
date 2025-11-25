import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import requests
import json
import time

# -----------------------------------------------------------------------------
# 1. API CONFIGURATION (User must set these!)
# -----------------------------------------------------------------------------
# Get your key from aistudio.google.com
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")

# Configure GenAI
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    pass

# -----------------------------------------------------------------------------
# 2. GENERATION LOGIC (The "Magic" Functions)
# -----------------------------------------------------------------------------

def generate_hype_card(game_data):
    """
    Uses 'Nano Banana Pro' (Gemini 3 Image) to generate a betting card.
    """
    # 1. Construct the Perfect Prompt
    # We use "Nano Banana Pro" specific triggering keywords like 'hyper-legible text'
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

    try:
        # In 2025, the model tag is often 'gemini-3-pro-image-preview' or 'nano-banana-pro-v1'
        # We use the standard GenAI python wrapper
        model = genai.ImageGenerationModel("gemini-3-pro-image-preview")
        
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter="block_only_high",
        )
        return response.images[0]  # Returns the PIL image
    except Exception as e:
        st.error(f"Image Gen Failed: {e}")
        return None


def generate_notebook_video(game_data):
    """
    Simulates calling the NotebookLM 'Video Overview' API.
    """
    # NOTE: This endpoint is hypothetical based on the 'NotebookLM API' released in late 2025.
    # In reality, you might need to use the manual upload or a specific wrapper.
    url = "https://notebooklm.googleapis.com/v1beta/projects/YOUR_PROJECT/notebooks:generateVideo"
    
    payload = {
        "sources": [
            {"text": f"Matchup Analysis for {game_data['Home Team']} vs {game_data['Away Team']}."},
            {"text": f"The AI Model predicts {game_data['Prediction']} with {game_data['Confidence']}% confidence."},
            {"text": "Key factors: Quarterback efficiency, defensive DVOA, and injury reports favoring the pick."}
        ],
        "style": "Deep Dive",  # The viral podcast style
        "video_format": "Nano_Banana_Visuals"  # The new feature that adds video to audio
    }
    
    # We return a mock success for the dashboard demo since we don't have a live key
    time.sleep(3)  # Simulate processing
    return True


# -----------------------------------------------------------------------------
# 3. PAGE SETUP & CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GAMELOCK 2025", page_icon="🍌", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. DASHBOARD TABS
# -----------------------------------------------------------------------------
st.title("🍌 GAMELOCK AI | Nano Edition")

# Mock Data for Demo (Your real load_data() goes here)
df = pd.DataFrame([{
    "Home Team": "Lions", "Away Team": "Bears", 
    "Prediction": "Lions", "Confidence": 88.5, "Odds": "-140"
}])

tab_bet, tab_media = st.tabs(["📋 Betting Data", "🎬 Media Studio"])

with tab_bet:
    st.dataframe(df, use_container_width=True)

with tab_media:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Select a game to generate content")
        selected_game_index = st.selectbox("Choose Game", df.index, format_func=lambda x: f"{df.iloc[x]['Home Team']} vs {df.iloc[x]['Away Team']}")
        game_data = df.iloc[selected_game_index]
        
        st.divider()
        
        # IMAGE GENERATION BUTTON
        if st.button("🎨 Generate Hype Card (Nano Banana Pro)", type="primary"):
            with st.spinner("Rendering 4K graphics with Gemini 3..."):
                img = generate_hype_card(game_data)
                if img:
                    st.session_state['last_image'] = img
                    st.success("Card Generated!")
        
        # VIDEO GENERATION BUTTON
        if st.button("🎥 Generate NotebookLM Deep Dive"):
            with st.spinner("AI Hosts are discussing the matchup..."):
                res = generate_notebook_video(game_data)
                st.session_state['video_ready'] = True
                st.success("Video Analysis Ready!")

    with col2:
        # DISPLAY AREA
        st.markdown('<div class="hype-container"><div class="hype-title">Content Preview</div></div>', unsafe_allow_html=True)
        
        if 'last_image' in st.session_state:
            st.image(st.session_state['last_image'], caption="Generated by Nano Banana Pro", use_container_width=True)
            st.download_button("Download Card", data="fake_bytes", file_name="bet_card.png")
            
        if 'video_ready' in st.session_state:
            st.markdown("### 🎧 AI Analysis Video")
            # In a real app, this would be the URL from the API
            st.video("https://www.w3schools.com/html/mov_bbb.mp4", format="video/mp4")
            st.caption("Hosts: 'Deep Dive' Audio + Nano Banana Visuals")
