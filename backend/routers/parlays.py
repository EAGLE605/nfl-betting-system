"""Parlays Router - Featured and custom parlay building.

Endpoints:
- GET /api/parlays/featured - Get pre-built parlay options
- POST /api/parlays/custom - Create a custom parlay from selected legs
"""

from typing import List
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, field_validator

from ..services.data_service import get_data_service


router = APIRouter(prefix="/api/parlays", tags=["parlays"])


# ==================== Response Models ====================

class ParlayLeg(BaseModel):
    """Single leg of a parlay."""
    game_id: str
    game: str
    pick: str
    odds: int = Field(description="American odds for this leg")
    prob: float = Field(description="Model probability")
    edge: float = Field(description="Edge vs market")
    leg_type: str = Field(description="spread, moneyline, total, prop")
    confidence: str


class ParlayResponse(BaseModel):
    """Single parlay response."""
    parlay_id: str
    name: str
    parlay_type: str
    legs: List[ParlayLeg]
    combined_odds: int = Field(description="Combined American odds")
    implied_prob: float = Field(description="Market implied probability")
    model_prob: float = Field(description="Our model probability")
    expected_value: float = Field(description="Expected value")
    risk_level: str = Field(description="conservative, moderate, aggressive")
    recommended_units: float = Field(description="Recommended bet size")


class FeaturedParlaysResponse(BaseModel):
    """Response for featured parlays endpoint."""
    parlays: List[ParlayResponse]
    total_parlays: int
    best_ev_parlay: str = Field(description="Name of parlay with best expected value")


class CustomParlayRequest(BaseModel):
    """Request body for custom parlay creation."""
    leg_ids: List[str] = Field(
        min_length=2,
        max_length=6,
        description="List of game/pick IDs to include in parlay"
    )

    @field_validator('leg_ids')
    @classmethod
    def validate_leg_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Duplicate leg IDs not allowed')
        return v


# ==================== Endpoints ====================

@router.get("/featured", response_model=FeaturedParlaysResponse)
async def get_featured_parlays():
    """
    Get pre-built featured parlay options.

    Returns multiple parlay strategies:
    - **Conservative**: 2-leg parlay with highest confidence picks
    - **Standard**: 3-leg balanced parlay
    - **Moneyline**: Favorite ML parlay for higher probability
    - **Underdog**: High-risk/high-reward underdog special

    All parlays are built from picks with identified edge.
    We don't parlay random games just for juice.

    Returns:
        List of featured parlays with analysis.
    """
    try:
        service = get_data_service()
        parlays = service.get_featured_parlays()

        if not parlays:
            return FeaturedParlaysResponse(
                parlays=[],
                total_parlays=0,
                best_ev_parlay="None available"
            )

        # Find best EV parlay
        best_ev = max(parlays, key=lambda p: p.get('expected_value', 0))

        return FeaturedParlaysResponse(
            parlays=[ParlayResponse(**p) for p in parlays],
            total_parlays=len(parlays),
            best_ev_parlay=best_ev.get('name', 'unknown'),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching featured parlays: {str(e)}")


@router.post("/custom", response_model=ParlayResponse)
async def create_custom_parlay(
    request: CustomParlayRequest = Body(
        examples=[{"leg_ids": ["demo_1", "demo_2", "demo_3"]}]
    )
):
    """
    Create a custom parlay from selected legs.

    Build your own parlay by selecting specific game picks.
    The system will calculate combined odds and expected value.

    Constraints:
    - Minimum 2 legs
    - Maximum 6 legs
    - No duplicate legs
    - All legs must be valid game IDs

    Args:
        request: CustomParlayRequest with leg_ids

    Returns:
        Complete parlay with odds and analysis.
    """
    try:
        service = get_data_service()
        parlay = service.create_custom_parlay(request.leg_ids)
        return ParlayResponse(**parlay)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating custom parlay: {str(e)}")


@router.get("/strategies")
async def get_parlay_strategies():
    """
    Get information about parlay building strategies.

    Educational endpoint about different parlay approaches.
    """
    return {
        'strategies': {
            'conservative': {
                'legs': 2,
                'description': 'Lower variance, higher hit rate',
                'typical_odds': '+250 to +300',
                'recommended_units': 1.0,
                'best_for': 'Consistent small wins',
            },
            'standard': {
                'legs': 3,
                'description': 'Balanced risk/reward',
                'typical_odds': '+500 to +700',
                'recommended_units': 0.5,
                'best_for': 'Regular parlay players',
            },
            'aggressive': {
                'legs': '4-6',
                'description': 'High risk, high reward',
                'typical_odds': '+1000 to +5000',
                'recommended_units': 0.25,
                'best_for': 'Small stakes, big potential',
            },
            'moneyline': {
                'legs': '2-3 favorites',
                'description': 'Higher probability but lower odds',
                'typical_odds': '+150 to +300',
                'recommended_units': 1.0,
                'best_for': 'Those who want frequent wins',
            },
            'underdog': {
                'legs': '2-3 dogs',
                'description': 'All underdog picks with edge',
                'typical_odds': '+800 to +2000',
                'recommended_units': 0.25,
                'best_for': 'Long shot players',
            },
        },
        'general_tips': [
            'Only parlay picks where you have identified edge',
            'Dont parlay correlated outcomes (e.g., team win + team over)',
            'Understand that parlays favor the house mathematically',
            'Use small unit sizes - these are for fun',
            'Consider same-game parlays (SGPs) for intentional correlation',
        ],
        'math': {
            '2_leg_breakeven': '27.5% (at -110 each)',
            '3_leg_breakeven': '14.3% (at -110 each)',
            '4_leg_breakeven': '7.4% (at -110 each)',
            'house_edge': 'Increases with each leg due to compounding vig',
        },
    }


@router.get("/available-legs")
async def get_available_legs():
    """
    Get all available legs for custom parlay building.

    Returns current week's picks that can be included in custom parlays.
    """
    try:
        service = get_data_service()
        picks = service.get_weekly_picks()

        legs = [
            {
                'leg_id': p['game_id'],
                'game': p['game'],
                'pick': p['pick'],
                'confidence': p['confidence'],
                'historical_rate': p['historical_rate'],
            }
            for p in picks
        ]

        return {
            'available_legs': legs,
            'total_available': len(legs),
            'min_legs': 2,
            'max_legs': 6,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching available legs: {str(e)}")
