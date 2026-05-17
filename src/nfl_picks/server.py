"""FastAPI server for NFL Picks PWA."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .core import Pick, PickSignal, Predictor

app = FastAPI(
    title="NFL Picks API",
    description="High-confidence NFL picks with 65.6% validated accuracy",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
APP_DIR = Path(__file__).parent.parent.parent / "app"
STATIC_DIR = APP_DIR / "static"

# Cache predictor instance
_predictor: Optional[Predictor] = None


def get_predictor() -> Predictor:
    """Get or create predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = Predictor()
    return _predictor


@app.get("/api/picks")
async def get_picks(
    season: int = Query(default=2026),
    week: int = Query(default=1, ge=1, le=18),
):
    """Get picks for a specific week."""
    try:
        predictor = get_predictor()
        picks = predictor.predict_week(season, week)

        actionable = [p for p in picks if p.signal != PickSignal.SKIP]

        return {
            "season": season,
            "week": week,
            "picks": [
                {
                    "game_id": p.game_id,
                    "season": p.season,
                    "week": p.week,
                    "home_team": p.home_team,
                    "away_team": p.away_team,
                    "pick_team": p.pick_team,
                    "pick_type": p.pick_type,
                    "line": p.line,
                    "confidence": p.confidence,
                    "signal": p.signal.value,
                    "reasons": p.reasons,
                    "deep_links": generate_deep_links(p),
                }
                for p in actionable
            ],
            "summary": {
                "strong": len([p for p in actionable if p.signal == PickSignal.STRONG]),
                "lean": len([p for p in actionable if p.signal == PickSignal.LEAN]),
                "total": len(picks),
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "picks": []},
        )


@app.get("/api/history")
async def get_history():
    """Get pick history with outcomes."""
    if not settings.picks_file.exists():
        return {"picks": [], "stats": {}}

    with open(settings.picks_file) as f:
        history = json.load(f)

    picks = [Pick.from_dict(h) for h in history]
    wins = sum(1 for p in picks if p.outcome == "W")
    losses = sum(1 for p in picks if p.outcome == "L")

    roi = 0.0
    if wins + losses > 0:
        roi = (wins * 0.91 - losses) / (wins + losses) * 100

    return {
        "picks": history,
        "stats": {
            "wins": wins,
            "losses": losses,
            "pending": sum(1 for p in picks if p.outcome is None),
            "roi": round(roi, 1),
            "win_rate": round(wins / (wins + losses) * 100, 1) if wins + losses else 0,
        },
    }


@app.get("/api/stats")
async def get_stats():
    """Get overall system stats."""
    history_data = await get_history()
    return {
        "model_version": "v4-rb-ngs",
        "validated_accuracy": 65.6,
        "validated_roi": 25.3,
        "sample_size": 317,
        "history": history_data["stats"],
    }


def generate_deep_links(pick: Pick) -> dict:
    """Generate sportsbook deep links for a pick."""
    matchup = f"{pick.away_team} {pick.home_team}"
    query = matchup.replace(" ", "%20")

    return {
        "draftkings": {
            "web": f"https://sportsbook.draftkings.com/leagues/football/nfl?search={query}",
            "app": f"dksb://sb/search/{query}",
        },
        "fanduel": {
            "web": f"https://sportsbook.fanduel.com/navigation/nfl?search={query}",
            "app": f"https://sportsbook.fanduel.com/navigation/nfl?search={query}",
        },
    }


# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest."""
    return FileResponse(APP_DIR / "manifest.json")


@app.get("/sw.js")
async def service_worker():
    """Serve service worker."""
    return FileResponse(APP_DIR / "sw.js", media_type="application/javascript")


@app.get("/")
@app.get("/{path:path}")
async def serve_app(path: str = ""):
    """Serve the PWA."""
    return FileResponse(APP_DIR / "index.html")


def run():
    """Run the server."""
    import uvicorn
    uvicorn.run(
        "nfl_picks.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
