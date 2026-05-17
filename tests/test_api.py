"""Tests for FastAPI server."""

import sys
from pathlib import Path

import pytest

# Add src to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestDeepLinks:
    """Tests for sportsbook deep links."""

    def test_generate_deep_links(self):
        from nfl_picks.core import Pick, PickSignal
        from nfl_picks.server import generate_deep_links

        pick = Pick(
            game_id="2026_01_KC_BAL",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            confidence=71.2,
            signal=PickSignal.STRONG,
        )

        links = generate_deep_links(pick)

        assert "draftkings" in links
        assert "fanduel" in links
        assert "web" in links["draftkings"]
        assert "app" in links["draftkings"]
        assert "BAL" in links["draftkings"]["web"]
        assert "KC" in links["draftkings"]["web"]


class TestAPIEndpoints:
    """Tests for API endpoints (requires test client)."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from nfl_picks.server import app
        return TestClient(app)

    def test_stats_endpoint(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["model_version"] == "v4-rb-ngs"
        assert data["validated_accuracy"] == 65.6
        assert data["validated_roi"] == 25.3

    def test_history_endpoint_empty(self, client):
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "picks" in data
        assert "stats" in data

    def test_serve_app(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"NFL Picks" in response.content

    def test_manifest(self, client):
        response = client.get("/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NFL Picks"
        assert data["display"] == "standalone"

    def test_service_worker(self, client):
        response = client.get("/sw.js")
        assert response.status_code == 200
        assert b"nfl-picks-v1" in response.content
