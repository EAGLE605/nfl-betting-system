"""Picks Router - Weekly and daily high-accuracy picks.

Endpoints:
- GET /api/picks/weekly - Get picks for the current/specified week
- GET /api/picks/today - Get picks for today's games only
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.data_service import get_data_service


router = APIRouter(prefix="/api/picks", tags=["picks"])


# ==================== Response Models ====================

class PickResponse(BaseModel):
    """Single pick response."""
    game_id: str
    game: str = Field(description="Game matchup (e.g., 'BUF @ KC')")
    pick: str = Field(description="The pick (e.g., 'BUF +3')")
    pick_team: str
    spread: float
    angle_name: str = Field(description="Betting angle that triggered this pick")
    historical_rate: float = Field(description="Historical win rate for this angle")
    sample_info: str = Field(description="Sample size info (e.g., '37-15-1 since 2014')")
    confidence: str = Field(description="Confidence level: elite, strong, solid, lean")
    fun_factor: int = Field(ge=1, le=5, description="Entertainment value 1-5")
    recommended_units: float = Field(description="Recommended bet size in units")
    notes: str


class WeeklyPicksResponse(BaseModel):
    """Response for weekly picks endpoint."""
    week: Optional[int] = None
    picks: List[PickResponse]
    total_picks: int
    elite_count: int = Field(description="Number of elite confidence picks")
    strong_count: int = Field(description="Number of strong confidence picks")


class TodayPicksResponse(BaseModel):
    """Response for today's picks endpoint."""
    date: str
    picks: List[PickResponse]
    total_picks: int


# ==================== Endpoints ====================

@router.get("/weekly", response_model=WeeklyPicksResponse)
async def get_weekly_picks(
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number (1-18)")
):
    """
    Get high-accuracy picks for the specified week.

    These picks are based on documented 60%+ win rate angles including:
    - Divisional underdogs (71% ATS since 2014)
    - Fade heavy public (63.3% win rate)
    - Road favorites off bye (60.8% ATS)
    - Week 1 divisional home underdogs (79.3% ATS)

    Args:
        week: NFL week number (1-18). If not specified, returns current week.

    Returns:
        Weekly picks with confidence levels and historical performance data.
    """
    try:
        service = get_data_service()
        picks = service.get_weekly_picks(week)

        # Count by confidence
        elite_count = sum(1 for p in picks if p.get('confidence') == 'elite')
        strong_count = sum(1 for p in picks if p.get('confidence') == 'strong')

        return WeeklyPicksResponse(
            week=week,
            picks=[PickResponse(**p) for p in picks],
            total_picks=len(picks),
            elite_count=elite_count,
            strong_count=strong_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly picks: {str(e)}")


@router.get("/today", response_model=TodayPicksResponse)
async def get_today_picks():
    """
    Get high-accuracy picks for today's games only.

    Filters the weekly picks to only include games scheduled for today.
    Useful for quick access to actionable picks.

    Returns:
        Today's picks with full analysis details.
    """
    try:
        from datetime import date

        service = get_data_service()
        picks = service.get_today_picks()

        return TodayPicksResponse(
            date=date.today().isoformat(),
            picks=[PickResponse(**p) for p in picks],
            total_picks=len(picks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's picks: {str(e)}")


@router.get("/angles")
async def get_available_angles():
    """
    Get information about all available betting angles.

    Returns documented angles with their historical performance.
    """
    angles = {
        'divisional_underdog': {
            'name': 'Divisional Underdog',
            'description': 'Divisional underdogs cover at elite rate',
            'historical_rate': 0.71,
            'sample': '37-15-1 since 2014',
            'confidence': 'elite',
        },
        'div_home_dog_week1': {
            'name': 'Week 1 Divisional Home Dog',
            'description': 'Best angle of the season - divisional home underdogs Week 1',
            'historical_rate': 0.793,
            'sample': '23-6 since 2009',
            'confidence': 'elite',
        },
        'div_road_dog_small': {
            'name': 'Small Divisional Road Dog',
            'description': 'Divisional road dogs of 6.5 points or less',
            'historical_rate': 0.724,
            'sample': '21-8-1 since 2013',
            'confidence': 'elite',
        },
        'div_dog_low_total': {
            'name': 'Divisional Dog + Low Total',
            'description': 'Divisional underdog with game total 42 or under',
            'historical_rate': 0.596,
            'sample': '84-57-4 last 5 years',
            'confidence': 'strong',
        },
        'road_fav_off_bye': {
            'name': 'Road Favorite Off Bye',
            'description': 'Road favorites coming off bye week',
            'historical_rate': 0.608,
            'sample': 'Since 1999',
            'confidence': 'strong',
        },
        'fade_heavy_public': {
            'name': 'Fade Heavy Public',
            'description': 'Bet against teams getting 60%+ public action',
            'historical_rate': 0.633,
            'sample': '2024 early season',
            'confidence': 'strong',
        },
        'early_season_big_dog': {
            'name': 'Early Season Big Underdog',
            'description': 'Weeks 1-3 underdogs of 5.5+ points',
            'historical_rate': 0.867,
            'sample': '13-2 ATS weeks 1-3 2024',
            'confidence': 'elite',
        },
    }

    return {
        'angles': angles,
        'sources': [
            'NxtBets: https://nxtbets.com/most-consistent-nfl-betting-trends-for-2025/',
            'Odds Shark: https://www.oddsshark.com/nfl/trends',
            'VSiN: https://vsin.com/nfl/seven-successful-nfl-week-1-betting-systems/',
            'BetMGM research'
        ]
    }
