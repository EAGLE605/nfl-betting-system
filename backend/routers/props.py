"""Props Router - Player props and trending props.

Endpoints:
- GET /api/props/player/{player_id} - Get props for a specific player
- GET /api/props/trending - Get trending props with high hit rates
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ..services.data_service import get_data_service


router = APIRouter(prefix="/api/props", tags=["props"])


# ==================== Response Models ====================

class PropDetail(BaseModel):
    """Single prop projection detail."""
    prop_type: str = Field(description="Type: pass_yards, rush_yards, receptions, etc.")
    line: float = Field(description="Book's line")
    projection: float = Field(description="Our projected value")
    direction: str = Field(description="over or under")
    confidence: str = Field(description="high, medium, low")
    edge: float = Field(description="Edge vs book line")


class PlayerPropsResponse(BaseModel):
    """Response for player props endpoint."""
    player_id: str
    player_name: str
    props: List[PropDetail]
    last_updated: str


class TrendingProp(BaseModel):
    """Single trending prop."""
    player: str
    team: str
    prop_type: str
    line: float
    direction: str
    hit_rate: float = Field(description="Historical hit rate (0-1)")
    sample_size: int = Field(description="Number of games in sample")
    streak: int = Field(description="Current streak (positive = hits)")
    confidence: str
    regression_risk: str = Field(description="Risk of regression: high, medium, low")
    trend_display: str = Field(description="Human-readable trend info")
    recommendation: str


class TrendingPropsResponse(BaseModel):
    """Response for trending props endpoint."""
    props: List[TrendingProp]
    total_props: int
    high_confidence_count: int
    warning: str = Field(
        default="Hot streaks often regress. Larger samples (15+ games) are more reliable.",
        description="Risk warning"
    )


# ==================== Endpoints ====================

@router.get("/player/{player_id}", response_model=PlayerPropsResponse)
async def get_player_props(
    player_id: str = Path(
        description="Player identifier (e.g., 'patrick_mahomes', 'travis_kelce')"
    )
):
    """
    Get prop projections for a specific player.

    Projections are based on:
    - Season averages (40% weight)
    - Recent form - last 3 games (30% weight)
    - Matchup factors - opponent defense rank (20% weight)
    - Game environment - home/away, dome/outdoor (10% weight)

    Args:
        player_id: Player name or ID (underscore-separated)

    Returns:
        Prop projections with confidence levels and edge calculations.
    """
    try:
        service = get_data_service()
        result = service.get_player_props(player_id)

        return PlayerPropsResponse(
            player_id=result['player_id'],
            player_name=result['player_name'],
            props=[PropDetail(**p) for p in result['props']],
            last_updated=result['last_updated'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching player props: {str(e)}")


@router.get("/trending", response_model=TrendingPropsResponse)
async def get_trending_props(
    min_hit_rate: float = Query(0.51, ge=0.0, le=1.0, description="Minimum hit rate filter"),
    min_sample: int = Query(5, ge=1, description="Minimum sample size"),
):
    """
    Get trending props with high historical hit rates.

    Identifies props where a player has exceeded the line at a high rate,
    filtering for statistical significance.

    Key insight: 51%+ hit rate in 10+ game samples overcomes standard vig.

    Warning: "100% last 5 games" trends often regress to mean. Use caution.

    Args:
        min_hit_rate: Minimum hit rate (default 0.51 to overcome -110 vig)
        min_sample: Minimum number of games in sample

    Returns:
        List of trending props sorted by confidence.
    """
    try:
        service = get_data_service()
        props = service.get_trending_props()

        # Apply filters
        filtered = [
            p for p in props
            if p['hit_rate'] >= min_hit_rate and p['sample_size'] >= min_sample
        ]

        # Count high confidence
        high_conf = sum(1 for p in filtered if p['confidence'] == 'high')

        return TrendingPropsResponse(
            props=[TrendingProp(**p) for p in filtered],
            total_props=len(filtered),
            high_confidence_count=high_conf,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending props: {str(e)}")


@router.get("/types")
async def get_prop_types():
    """
    Get information about available prop types.

    Returns prop categories and typical lines.
    """
    return {
        'prop_types': {
            'passing': [
                {'type': 'pass_yards', 'typical_range': '200-350'},
                {'type': 'pass_tds', 'typical_range': '1.5-2.5'},
                {'type': 'completions', 'typical_range': '18-28'},
                {'type': 'pass_attempts', 'typical_range': '28-40'},
                {'type': 'interceptions', 'typical_range': '0.5-1.5'},
            ],
            'rushing': [
                {'type': 'rush_yards', 'typical_range': '40-100'},
                {'type': 'rush_attempts', 'typical_range': '12-22'},
                {'type': 'rush_tds', 'typical_range': '0.5'},
                {'type': 'longest_rush', 'typical_range': '10-25'},
            ],
            'receiving': [
                {'type': 'receiving_yards', 'typical_range': '40-100'},
                {'type': 'receptions', 'typical_range': '3-8'},
                {'type': 'receiving_tds', 'typical_range': '0.5'},
                {'type': 'targets', 'typical_range': '5-12'},
            ],
            'scoring': [
                {'type': 'anytime_td', 'description': 'Score a TD anytime'},
                {'type': 'first_td', 'description': 'Score first TD of game'},
            ],
        },
        'hit_rate_guidance': {
            '51%': 'Minimum to overcome -110 standard vig',
            '53%': 'Small but consistent edge',
            '55%+': 'Strong actionable edge',
            '60%+': 'Excellent - but verify sample size',
        },
    }


@router.get("/correlations")
async def get_prop_correlations():
    """
    Get information about prop correlations for SGP building.

    Understanding correlations is key to building profitable SGPs.
    """
    return {
        'positive_correlations': [
            {
                'props': ['pass_yards', 'game_over'],
                'strength': 0.35,
                'explanation': 'High-scoring games mean more passing opportunities'
            },
            {
                'props': ['team_win', 'rush_yards'],
                'strength': 0.25,
                'explanation': 'Winning teams run more to kill clock'
            },
            {
                'props': ['pass_yards', 'receiving_yards'],
                'strength': 0.40,
                'explanation': 'QB success correlates with WR success'
            },
            {
                'props': ['rush_attempts', 'team_favored'],
                'strength': 0.20,
                'explanation': 'Favorites run more with lead'
            },
        ],
        'negative_correlations': [
            {
                'props': ['interceptions', 'team_win'],
                'strength': -0.30,
                'explanation': 'Turnovers hurt win probability'
            },
            {
                'props': ['game_under', 'pass_yards_over'],
                'strength': -0.25,
                'explanation': 'Low-scoring games limit passing stats'
            },
        ],
        'sgp_tips': [
            'Correlate props within the same team when possible',
            'Game script props (winner, margin) correlate with individual stats',
            'High totals favor OVER props across the board',
            'Be cautious pairing props that rely on limited touches'
        ],
    }
