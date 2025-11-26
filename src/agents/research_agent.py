"""
Autonomous Research Agent

Uses Perplexity API (with web search) to autonomously research:
- Injury updates
- Weather impacts
- Line movements
- Public betting trends
- Historical matchup patterns
- News and narratives

Provides real-time intelligence for betting decisions.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result from a research query."""

    query: str
    answer: str
    sources: List[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    citations: List[Dict[str, str]] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)


@dataclass
class GameIntelligence:
    """Compiled intelligence for a game."""

    game_id: str
    home_team: str
    away_team: str
    injury_report: Dict[str, List[str]]
    weather_impact: str
    line_movement: Dict[str, Any]
    public_sentiment: Dict[str, float]
    key_narratives: List[str]
    sharp_action: str
    historical_trends: List[str]
    expert_opinions: List[str]
    confidence_factors: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


class ResearchAgent:
    """
    Autonomous research agent using Perplexity API.

    Perplexity provides:
    - Real-time web search
    - Source citations
    - Synthesized answers

    Perfect for getting latest injury news, public sentiment, etc.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.client = httpx.AsyncClient(timeout=60.0)

        # Default model - online version searches the web
        self.model = "llama-3.1-sonar-large-128k-online"

        # Research cache to avoid duplicate queries
        self.cache: Dict[str, ResearchResult] = {}
        self.cache_ttl_minutes = 30

        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not set - research agent disabled")

    async def _query_perplexity(
        self, query: str, system_prompt: str = ""
    ) -> Dict[str, Any]:
        """Execute a query against Perplexity API."""
        if not self.api_key:
            return {"error": "API key not configured"}

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": query})

            response = await self.client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.2,  # Low for factual accuracy
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()

            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "citations": data.get("citations", []),
                "usage": data.get("usage", {}),
            }

        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            return {"error": str(e)}

    async def research_query(self, query: str) -> ResearchResult:
        """
        Execute a general research query.

        Args:
            query: The question to research

        Returns:
            ResearchResult with answer and sources
        """
        # Check cache
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = (datetime.now() - cached.timestamp).total_seconds() / 60
            if age < self.cache_ttl_minutes:
                logger.info(f"[CACHE] Using cached result for: {query[:50]}...")
                return cached

        system = """You are an expert sports betting research assistant. 
Provide factual, data-driven answers with specific numbers and dates when available.
Always cite your sources. Focus on actionable betting intelligence."""

        result = await self._query_perplexity(query, system)

        if "error" in result:
            return ResearchResult(
                query=query,
                answer=f"Research failed: {result['error']}",
                sources=[],
                confidence=0.0,
            )

        research_result = ResearchResult(
            query=query,
            answer=result["content"],
            sources=result.get("citations", []),
            confidence=0.8,  # Perplexity generally reliable
        )

        # Cache result
        self.cache[cache_key] = research_result

        return research_result

    async def get_injury_report(self, team: str) -> Dict[str, Any]:
        """
        Get latest injury report for a team.

        Args:
            team: Team name (e.g., "Kansas City Chiefs")

        Returns:
            Dict with injury information
        """
        query = f"""What is the current injury report for the {team}? 
List all players on the injury report with their:
1. Name
2. Position
3. Injury type
4. Status (Out, Doubtful, Questionable, Probable)
5. Impact on team's performance

Focus on injuries from the last 7 days. Include practice participation status."""

        result = await self.research_query(query)

        # Parse into structured format
        return {
            "team": team,
            "report": result.answer,
            "sources": result.sources,
            "timestamp": result.timestamp.isoformat(),
        }

    async def get_line_movement(self, game: str) -> Dict[str, Any]:
        """
        Get line movement analysis for a game.

        Args:
            game: Game description (e.g., "Chiefs vs Bills Week 12")

        Returns:
            Dict with line movement analysis
        """
        query = f"""Analyze the betting line movement for {game}:
1. Opening line vs current line (spread and total)
2. Direction of movement
3. Any reverse line movement (line moving opposite to heavy betting)
4. Sharp vs public money indicators
5. Key numbers and thresholds

Include data from multiple sportsbooks if available."""

        result = await self.research_query(query)

        return {
            "game": game,
            "analysis": result.answer,
            "sources": result.sources,
            "timestamp": result.timestamp.isoformat(),
        }

    async def get_public_sentiment(self, team1: str, team2: str) -> Dict[str, Any]:
        """
        Get public betting sentiment for a matchup.

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            Dict with public sentiment analysis
        """
        query = f"""What is the public betting sentiment for {team1} vs {team2}?
Include:
1. Percentage of bets on each side (spread, moneyline, total)
2. Percentage of money on each side
3. Any divergence between bet count and money (sharp indicator)
4. Social media/fan sentiment
5. Expert picks and consensus"""

        result = await self.research_query(query)

        return {
            "matchup": f"{team1} vs {team2}",
            "sentiment": result.answer,
            "sources": result.sources,
            "timestamp": result.timestamp.isoformat(),
        }

    async def get_weather_impact(self, venue: str, game_time: str) -> Dict[str, Any]:
        """
        Get weather forecast and impact analysis for a game.

        Args:
            venue: Stadium name and location
            game_time: Game date/time

        Returns:
            Dict with weather analysis
        """
        query = f"""What is the weather forecast for {venue} on {game_time}?
Analyze:
1. Temperature, wind speed, precipitation
2. Historical scoring in similar conditions at this venue
3. Impact on passing game, kicking game
4. Which team is more suited to these conditions
5. Any weather advantages/disadvantages"""

        result = await self.research_query(query)

        return {
            "venue": venue,
            "game_time": game_time,
            "analysis": result.answer,
            "sources": result.sources,
            "timestamp": result.timestamp.isoformat(),
        }

    async def get_historical_trends(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Get historical betting trends.

        Args:
            query_type: Type of trend ("h2h", "ats", "situational", "division")
            **kwargs: Additional parameters

        Returns:
            Dict with historical analysis
        """
        if query_type == "h2h":
            team1 = kwargs.get("team1", "")
            team2 = kwargs.get("team2", "")
            query = f"""Historical head-to-head betting trends for {team1} vs {team2}:
1. ATS record last 10 meetings
2. Over/under trends
3. Average margin of victory
4. Home/away split
5. Any notable streaks or patterns"""

        elif query_type == "situational":
            situation = kwargs.get("situation", "")
            query = f"""Historical betting trends for: {situation}
Include:
1. ATS record in this situation
2. Sample size and significance
3. Notable exceptions
4. Recent trend changes
5. Key factors driving the pattern"""

        elif query_type == "division":
            division = kwargs.get("division", "")
            query = f"""Betting trends for {division} divisional games:
1. Favorite/underdog ATS performance
2. Home/away ATS splits
3. Totals trends
4. Rivalry game patterns
5. Recent season trends"""

        else:
            query = f"NFL betting trends for: {kwargs.get('topic', 'general')}"

        result = await self.research_query(query)

        return {
            "query_type": query_type,
            "parameters": kwargs,
            "analysis": result.answer,
            "sources": result.sources,
            "timestamp": result.timestamp.isoformat(),
        }

    async def compile_game_intelligence(
        self,
        home_team: str,
        away_team: str,
        venue: str,
        game_time: str,
        game_id: str = "",
    ) -> GameIntelligence:
        """
        Compile comprehensive intelligence for a game.

        Runs all research queries in parallel for efficiency.

        Args:
            home_team: Home team name
            away_team: Away team name
            venue: Stadium name
            game_time: Game date/time
            game_id: Optional game ID

        Returns:
            GameIntelligence with all compiled research
        """
        logger.info(f"Compiling intelligence: {away_team} @ {home_team}")

        # Run all research in parallel
        tasks = [
            self.get_injury_report(home_team),
            self.get_injury_report(away_team),
            self.get_line_movement(f"{away_team} at {home_team}"),
            self.get_public_sentiment(away_team, home_team),
            self.get_weather_impact(venue, game_time),
            self.get_historical_trends("h2h", team1=home_team, team2=away_team),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Parse results
        home_injuries = results[0] if not isinstance(results[0], Exception) else {}
        away_injuries = results[1] if not isinstance(results[1], Exception) else {}
        line_movement = results[2] if not isinstance(results[2], Exception) else {}
        public_sentiment = results[3] if not isinstance(results[3], Exception) else {}
        weather = results[4] if not isinstance(results[4], Exception) else {}
        historical = results[5] if not isinstance(results[5], Exception) else {}

        # Extract key narratives
        key_narratives = []

        if home_injuries.get("report"):
            key_narratives.append(f"Home injuries: Check {home_team} injury report")
        if away_injuries.get("report"):
            key_narratives.append(f"Away injuries: Check {away_team} injury report")
        if "reverse line movement" in str(line_movement.get("analysis", "")).lower():
            key_narratives.append("SHARP ACTION DETECTED: Reverse line movement")

        # Calculate confidence factors
        confidence_factors = {
            "injury_data": 0.8 if home_injuries.get("report") else 0.3,
            "line_movement": 0.9 if line_movement.get("analysis") else 0.3,
            "public_sentiment": 0.7 if public_sentiment.get("sentiment") else 0.3,
            "weather_data": 0.8 if weather.get("analysis") else 0.5,
            "historical_data": 0.7 if historical.get("analysis") else 0.3,
        }

        return GameIntelligence(
            game_id=game_id or f"{away_team}_{home_team}_{game_time}",
            home_team=home_team,
            away_team=away_team,
            injury_report={
                "home": home_injuries.get("report", "No data"),
                "away": away_injuries.get("report", "No data"),
            },
            weather_impact=weather.get("analysis", "Indoor/No impact"),
            line_movement=line_movement,
            public_sentiment={
                "home_pct": 0.5,  # Would need to parse from sentiment
                "away_pct": 0.5,
                "details": public_sentiment.get("sentiment", "No data"),
            },
            key_narratives=key_narratives,
            sharp_action=line_movement.get("analysis", "No sharp action detected"),
            historical_trends=[historical.get("analysis", "No historical data")],
            expert_opinions=[],
            confidence_factors=confidence_factors,
        )

    async def ask(self, question: str) -> str:
        """
        Simple interface to ask any betting-related question.

        Args:
            question: Any question about NFL betting

        Returns:
            Researched answer
        """
        result = await self.research_query(question)
        return result.answer

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_research_agent: Optional[ResearchAgent] = None


def get_research_agent() -> ResearchAgent:
    """Get or create singleton ResearchAgent instance."""
    global _research_agent
    if _research_agent is None:
        _research_agent = ResearchAgent()
    return _research_agent


async def test_research_agent():
    """Test the research agent."""
    agent = get_research_agent()

    if not agent.api_key:
        print("Set PERPLEXITY_API_KEY to test research agent")
        return

    print("Testing Research Agent...")

    # Test simple query
    print("\n1. Testing simple query...")
    answer = await agent.ask("What are the key injuries for NFL Week 13 2024?")
    print(f"Answer: {answer[:500]}...")

    # Test injury report
    print("\n2. Testing injury report...")
    injuries = await agent.get_injury_report("Kansas City Chiefs")
    print(f"Chiefs injuries: {injuries['report'][:500]}...")

    # Test line movement
    print("\n3. Testing line movement...")
    lines = await agent.get_line_movement("Chiefs vs Bills Week 12")
    print(f"Line movement: {lines['analysis'][:500]}...")

    # Test full game intelligence
    print("\n4. Testing full game intelligence...")
    intel = await agent.compile_game_intelligence(
        home_team="Buffalo Bills",
        away_team="Kansas City Chiefs",
        venue="Highmark Stadium, Buffalo, NY",
        game_time="Sunday, November 24, 2024 4:25 PM ET",
    )

    print(f"\nGame Intelligence Report:")
    print(f"  Key narratives: {intel.key_narratives}")
    print(f"  Confidence factors: {intel.confidence_factors}")

    await agent.close()


if __name__ == "__main__":
    asyncio.run(test_research_agent())
