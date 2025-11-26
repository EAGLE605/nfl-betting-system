"""
GAMELOCK AI - Video Engine
Generates AI-narrated "Deep Dive" video breakdowns of bets.

Architecture:
1. Gemini (Brain) - Writes the TV script
2. Pillow (Artist) - Generates styled slide graphics
3. OpenAI TTS (Voice) - Generates narration audio
4. MoviePy (Editor) - Stitches into .mp4
"""

import os
import textwrap
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False


# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
def get_secret(key):
    """Get API key from environment or streamlit secrets."""
    import os

    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.environ.get(key, "")


# Team colors for styling
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
    "Dolphins": ("#008E97", "#FC4C02"),
    "Patriots": ("#002244", "#C60C30"),
    "Jets": ("#125740", "#000000"),
    "Raiders": ("#000000", "#A5ACAF"),
    "Chargers": ("#0080C6", "#FFC20E"),
    "Broncos": ("#FB4F14", "#002244"),
    "Texans": ("#03202F", "#A71930"),
    "Colts": ("#002C5F", "#A2AAAD"),
    "Titans": ("#0C2340", "#4B92DB"),
    "Jaguars": ("#006778", "#9F792C"),
    "Saints": ("#D3BC8D", "#101820"),
    "Falcons": ("#A71930", "#000000"),
    "Panthers": ("#0085CA", "#101820"),
    "Buccaneers": ("#D50A0A", "#FF7900"),
    "Cardinals": ("#97233F", "#000000"),
    "Rams": ("#003594", "#FFA300"),
    "Giants": ("#0B2265", "#A71930"),
    "Commanders": ("#5A1414", "#FFB612"),
    "Browns": ("#311D00", "#FF3C00"),
    "Steelers": ("#FFB612", "#101820"),
}


# -----------------------------------------------------------------------------
# 2. THE SCRIPT WRITER (Gemini or GPT)
# -----------------------------------------------------------------------------
def generate_script(game_data):
    """Generate a 30-second SportsCenter-style script."""

    prompt = f"""Write a 30-second exciting sports betting analysis script.

MATCHUP: {game_data['matchup']}
THE BET: {game_data['bet']} at {game_data['odds']}
CONFIDENCE: {game_data['confidence']}%

Structure it as:
1. HOOK (5 sec) - Excitement about the matchup
2. THE DATA (15 sec) - Why we love this bet, mention specific stats/trends
3. THE LOCK (10 sec) - Final verdict, confidence level

Rules:
- Return ONLY the spoken narration text
- No stage directions or labels
- Keep it punchy and energetic like ESPN
- Use betting terminology
- Be confident"""

    # Try Gemini first
    google_key = get_secret("GOOGLE_API_KEY")
    if GENAI_AVAILABLE and google_key:
        try:
            genai.configure(api_key=google_key)
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini failed: {e}")

    # Fallback to GPT
    openai_key = get_secret("OPENAI_API_KEY")
    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT failed: {e}")

    # Fallback script
    return f"""
    Welcome to the deep dive! We're breaking down {game_data['matchup']}.
    
    Tonight's lock: {game_data['bet']} at {game_data['odds']}.
    
    The numbers don't lie. Our model shows {game_data['confidence']}% confidence on this play.
    Sharp money has been pounding this line all week.
    
    This is a GAMELOCK. Let's cash this ticket!
    """


# -----------------------------------------------------------------------------
# 3. THE ARTIST (Pillow Graphics)
# -----------------------------------------------------------------------------
def create_gradient_background(width, height, color1, color2):
    """Create a gradient background image."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = tuple(int(color1.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    r2, g2, b2 = tuple(int(color2.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def add_neon_glow(draw, text, position, font, color, glow_color):
    """Add neon glow effect to text."""
    x, y = position
    # Draw glow layers
    for offset in range(8, 0, -2):
        alpha = 50 - offset * 5
        glow = (*tuple(int(glow_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)),)
        draw.text((x - offset, y), text, font=font, fill=glow)
        draw.text((x + offset, y), text, font=font, fill=glow)
        draw.text((x, y - offset), text, font=font, fill=glow)
        draw.text((x, y + offset), text, font=font, fill=glow)
    # Draw main text
    draw.text(position, text, font=font, fill=color)


def generate_slide(slide_type, game_data, filename, width=1920, height=1080):
    """Generate a styled slide image."""

    # Get team colors
    team = game_data.get("team", "Lions")
    colors = TEAM_COLORS.get(team, ("#0076B6", "#0a0f1a"))
    primary, secondary = colors

    # Create gradient background
    img = create_gradient_background(width, height, "#0a0f1a", "#1e293b")
    draw = ImageDraw.Draw(img)

    # Try to load fonts (fallback to default)
    try:
        font_large = ImageFont.truetype("arial.ttf", 120)
        font_medium = ImageFont.truetype("arial.ttf", 72)
        font_small = ImageFont.truetype("arial.ttf", 48)
    except:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # Add decorative elements
    # Top bar
    draw.rectangle([(0, 0), (width, 8)], fill=primary)
    # Bottom bar
    draw.rectangle([(0, height - 8), (width, height)], fill=primary)

    # Diagonal accent lines
    for i in range(0, width, 100):
        draw.line([(i, 0), (i + 200, height)], fill=primary, width=1)

    if slide_type == "title":
        # SLIDE 1: Title/Matchup
        draw.text(
            (width // 2 - 200, 100), "GAMELOCK AI", font=font_medium, fill="#22c55e"
        )
        draw.text((width // 2 - 350, 250), "DEEP DIVE", font=font_large, fill="#ffffff")

        # Matchup
        draw.rectangle(
            [(100, 450), (width - 100, 650)], fill=primary, outline="#ffffff", width=3
        )
        matchup_text = game_data["matchup"]
        draw.text(
            (width // 2 - len(matchup_text) * 20, 500),
            matchup_text,
            font=font_medium,
            fill="#ffffff",
        )

        # Subtitle
        draw.text(
            (width // 2 - 300, 750),
            "AI-POWERED ANALYSIS",
            font=font_small,
            fill="#94a3b8",
        )

    elif slide_type == "pick":
        # SLIDE 2: The Pick
        draw.text((width // 2 - 200, 100), "THE PICK", font=font_medium, fill="#22c55e")

        # Main bet display
        bet_text = game_data["bet"]
        draw.rectangle(
            [(200, 300), (width - 200, 550)], fill=primary, outline="#22c55e", width=5
        )
        draw.text(
            (width // 2 - len(bet_text) * 30, 370),
            bet_text,
            font=font_large,
            fill="#ffffff",
        )

        # Odds
        odds_text = f"ODDS: {game_data['odds']}"
        draw.text((width // 2 - 150, 620), odds_text, font=font_medium, fill="#22c55e")

        # Sharp indicator
        draw.text(
            (width // 2 - 200, 800),
            "SHARP MONEY APPROVED",
            font=font_small,
            fill="#f59e0b",
        )

    elif slide_type == "confidence":
        # SLIDE 3: Confidence/Lock
        draw.text(
            (width // 2 - 200, 100), "CONFIDENCE", font=font_medium, fill="#22c55e"
        )

        # Big percentage
        conf_text = f"{game_data['confidence']}%"
        draw.text((width // 2 - 180, 280), conf_text, font=font_large, fill="#22c55e")

        # Progress bar
        bar_width = int((width - 400) * (int(game_data["confidence"]) / 100))
        draw.rectangle(
            [(200, 550), (width - 200, 620)], fill="#1f2937", outline="#374151", width=2
        )
        draw.rectangle([(200, 550), (200 + bar_width, 620)], fill="#22c55e")

        # Lock text
        draw.rectangle(
            [(width // 2 - 200, 700), (width // 2 + 200, 800)], fill="#22c55e"
        )
        draw.text((width // 2 - 100, 720), "LOCKED IN", font=font_small, fill="#000000")

        # Footer
        draw.text(
            (width // 2 - 150, 900), "GAMELOCK AI", font=font_small, fill="#64748b"
        )

    img.save(filename)
    return filename


# -----------------------------------------------------------------------------
# 4. THE VOICE (OpenAI TTS)
# -----------------------------------------------------------------------------
def generate_audio(text, filename="narration.mp3"):
    """Generate narration audio using OpenAI TTS."""
    openai_key = get_secret("OPENAI_API_KEY")

    if not openai_key:
        raise ValueError("OpenAI API key required for TTS")

    client = OpenAI(api_key=openai_key)

    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="onyx",  # Deep, authoritative voice - like a sports announcer
        input=text,
    )

    response.stream_to_file(filename)
    return filename


# -----------------------------------------------------------------------------
# 5. THE EDITOR (MoviePy)
# -----------------------------------------------------------------------------
def create_video_bet(game_data, output_dir="."):
    """
    Main function to create a complete bet analysis video.

    Args:
        game_data: dict with keys: id, matchup, bet, odds, confidence, team
        output_dir: where to save the video

    Returns:
        path to the generated .mp4 file
    """

    if not MOVIEPY_AVAILABLE:
        raise ImportError("MoviePy not installed. Run: pip install moviepy")

    print(f"[VIDEO] Starting Video Generation for {game_data['matchup']}...")

    # Create temp directory
    temp_dir = Path(output_dir) / "temp_video"
    temp_dir.mkdir(exist_ok=True)

    try:
        # Step A: Write Script
        print("[SCRIPT] Writing script with AI...")
        script = generate_script(game_data)
        print(f"Script preview: {script[:100]}...")

        # Step B: Generate Audio
        print("[AUDIO] Recording narration...")
        audio_file = str(temp_dir / "narration.mp3")
        generate_audio(script, audio_file)

        # Step C: Generate Slides
        print("[GRAPHICS] Rendering slides...")
        slide1 = generate_slide("title", game_data, str(temp_dir / "slide1.png"))
        slide2 = generate_slide("pick", game_data, str(temp_dir / "slide2.png"))
        slide3 = generate_slide("confidence", game_data, str(temp_dir / "slide3.png"))

        # Step D: Assemble Video
        print("[EDITOR] Assembling video...")

        # Load audio to get duration
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration
        slide_duration = duration / 3

        # Create video clips from images
        clip1 = ImageClip(slide1).with_duration(slide_duration).with_fps(24)
        clip2 = ImageClip(slide2).with_duration(slide_duration).with_fps(24)
        clip3 = ImageClip(slide3).with_duration(slide_duration).with_fps(24)

        # Concatenate clips
        final_video = concatenate_videoclips([clip1, clip2, clip3], method="compose")
        final_video = final_video.with_audio(audio_clip)

        # Export
        output_filename = str(Path(output_dir) / f"bet_video_{game_data['id']}.mp4")
        final_video.write_videofile(
            output_filename,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,  # Suppress MoviePy output
        )

        # Close clips to release resources
        clip1.close()
        clip2.close()
        clip3.close()
        audio_clip.close()
        final_video.close()

        print(f"[DONE] Video Saved: {output_filename}")
        return output_filename

    finally:
        # Cleanup temp files
        import shutil

        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# -----------------------------------------------------------------------------
# TEST
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Test with mock data
    test_bet = {
        "id": "test_001",
        "matchup": "Lions vs Cowboys",
        "bet": "LIONS -3.5",
        "odds": "-110",
        "confidence": "92",
        "team": "Lions",
    }

    try:
        video_path = create_video_bet(test_bet)
        print(f"Success! Video at: {video_path}")
    except Exception as e:
        print(f"Error: {e}")
