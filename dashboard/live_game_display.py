"""
Live Game Display Components for Streamlit Dashboard

Reusable UI components for showing live NFL games.

BEGINNER-FRIENDLY: These are like LEGO blocks you can use to build
different views of games in your dashboard.
"""

from datetime import datetime
from typing import Dict, List

import streamlit as st


def render_game_card(game: Dict, show_predictions: bool = False):
    """
    Render a single game card with live status.

    BEGINNER NOTE: This creates a nice-looking card for one game.
    Shows team names, scores, and live status.

    Args:
        game: Game dictionary from LiveGameTracker
        show_predictions: Whether to show model predictions (future feature)
    """
    # Game status (live, final, upcoming)
    status = game.get("status", "")
    is_live = game.get("is_live", False)
    is_final = game.get("is_final", False)

    # Team info
    away_team = game.get("away_team", "")
    home_team = game.get("home_team", "")
    away_score = game.get("away_score", 0)
    home_score = game.get("home_score", 0)

    # Status display
    status_display = game.get("status_display", "")

    # Color coding
    if is_live:
        border_color = "🔴"
        bg_color = "#1e1e1e"
    elif is_final:
        border_color = "✅"
        bg_color = "#0f1419"
    else:
        border_color = "⏰"
        bg_color = "#0f1419"

    # Create columns for team vs team layout
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        # Away team
        st.markdown(f"### {away_team}")
        if is_live or is_final:
            st.markdown(
                f"<h1 style='text-align: right; margin: 0;'>{away_score}</h1>",
                unsafe_allow_html=True,
            )

    with col2:
        # Status in the middle
        st.markdown(
            f"<p style='text-align: center; color: #888;'>{status_display}</p>",
            unsafe_allow_html=True,
        )
        if not is_live and not is_final:
            st.markdown(
                "<p style='text-align: center; font-size: 0.8em;'>vs</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='text-align: center; font-size: 1.2em;'>@</p>",
                unsafe_allow_html=True,
            )

    with col3:
        # Home team
        st.markdown(f"### {home_team}")
        if is_live or is_final:
            st.markdown(
                f"<h1 style='text-align: left; margin: 0;'>{home_score}</h1>",
                unsafe_allow_html=True,
            )

    # Separator
    st.markdown("---")


def render_live_games_section(games: List[Dict]):
    """
    Render the "Live Now" section.

    BEGINNER NOTE: Shows all games currently in progress.
    If no games are live, shows a friendly message.

    Args:
        games: List of game dicts (should be filtered to live games only)
    """
    st.subheader("🔴 LIVE NOW")

    if not games:
        st.info("No games currently in progress. Check back during game days!")
        return

    st.markdown(f"**{len(games)} game(s) live**")

    for game in games:
        render_game_card(game)


def render_upcoming_games_section(games: List[Dict]):
    """
    Render the "Upcoming This Week" section.

    Args:
        games: List of game dicts (filtered to upcoming games)
    """
    st.subheader("⏰ UPCOMING THIS WEEK")

    if not games:
        st.info("No upcoming games this week.")
        return

    # Sort by game time
    games_sorted = sorted(games, key=lambda g: g.get("game_time_local", datetime.max))

    st.markdown(f"**{len(games_sorted)} game(s) scheduled**")

    for game in games_sorted:
        render_game_card(game)


def render_completed_games_section(games: List[Dict]):
    """
    Render the "Recently Completed" section.

    Args:
        games: List of game dicts (filtered to final games)
    """
    st.subheader("✅ RECENTLY COMPLETED")

    if not games:
        st.info("No recently completed games.")
        return

    # Sort by game time (most recent first)
    games_sorted = sorted(
        games, key=lambda g: g.get("game_time_local", datetime.min), reverse=True
    )

    st.markdown(f"**{len(games_sorted)} game(s) final**")

    for game in games_sorted:
        render_game_card(game)


def render_scoreboard_ticker(games: List[Dict]):
    """
    Render a compact scoreboard ticker (all live games in one line).

    BEGINNER NOTE: This is like the ESPN ticker at the bottom of TV.
    Shows all live scores in a compact format.

    Args:
        games: List of all games (will filter to live ones)
    """
    live_games = [g for g in games if g.get("is_live", False)]

    if not live_games:
        return

    ticker_html = "<div style='background: #1e1e1e; padding: 10px; border-radius: 5px; overflow-x: auto; white-space: nowrap;'>"
    ticker_html += "🔴 <b>LIVE:</b> &nbsp;&nbsp;"

    for i, game in enumerate(live_games):
        away = game.get("away_team", "")
        home = game.get("home_team", "")
        away_score = game.get("away_score", 0)
        home_score = game.get("home_score", 0)
        period = game.get("period", 1)
        clock = game.get("clock", "0:00")

        # Determine winning team (bold)
        if away_score > home_score:
            away_style = "font-weight: bold;"
            home_style = ""
        elif home_score > away_score:
            away_style = ""
            home_style = "font-weight: bold;"
        else:
            away_style = ""
            home_style = ""

        # Quarter display
        if period <= 4:
            quarter = f"Q{period}"
        elif period == 5:
            quarter = "OT"
        else:
            quarter = f"{period-4}OT"

        ticker_html += f"""
        <span style='margin-right: 30px;'>
            <span style='{away_style}'>{away} {away_score}</span>
            @
            <span style='{home_style}'>{home} {home_score}</span>
            <span style='color: #888; font-size: 0.8em;'>({quarter} {clock})</span>
        </span>
        """

        if i < len(live_games) - 1:
            ticker_html += " | "

    ticker_html += "</div>"

    st.markdown(ticker_html, unsafe_allow_html=True)


def render_auto_refresh_control():
    """
    Render auto-refresh controls.

    BEGINNER NOTE: Lets users manually refresh or see when auto-refresh is active.

    Returns:
        True if user clicked manual refresh button
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.caption("🔄 Auto-refresh during game windows (Thu/Sun/Mon)")

    with col2:
        # Last updated timestamp
        if "last_refresh" in st.session_state:
            time_ago = (datetime.now() - st.session_state.last_refresh).seconds // 60
            st.caption(f"Updated {time_ago}m ago")

    with col3:
        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            return True

    return False


def render_game_window_indicator(tracker):
    """
    Show if we're in an auto-refresh window.

    BEGINNER NOTE: Visual indicator that auto-refresh is active.

    Args:
        tracker: LiveGameTracker instance
    """
    should_refresh = tracker.should_auto_refresh()

    if should_refresh:
        st.success("🟢 Auto-refresh ACTIVE (Game window)")
    else:
        st.info("⚫ Auto-refresh PAUSED (Off-hours)")


def render_timezone_display(tracker):
    """
    Show the user's configured timezone.

    BEGINNER NOTE: So users know what timezone times are displayed in.

    Args:
        tracker: LiveGameTracker instance
    """
    tz_name = str(tracker.user_timezone)
    st.caption(f"📍 All times shown in: {tz_name}")
