"""
LLM Council - Multi-Model Consensus System

Implements Karpathy's LLM Council pattern for betting decisions:
1. Multiple LLMs independently analyze picks
2. Cross-review and rank each other's analysis
3. Chairman LLM synthesizes final decision

Supported providers: OpenAI, Anthropic, Grok (X.AI), Google, Perplexity
"""

import asyncio
import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    
    @property
    def is_valid(self) -> bool:
        return bool(self.api_key and self.model)


@dataclass
class CouncilMember:
    """A member of the LLM council."""
    member_id: str
    config: LLMConfig
    specialty: str = "general"  # e.g., "statistical", "situational", "contrarian"
    weight: float = 1.0
    recent_accuracy: float = 0.5
    total_votes: int = 0
    correct_votes: int = 0


@dataclass
class PickAnalysis:
    """Analysis from a single council member."""
    member_id: str
    pick: str  # "home", "away", "over", "under", "pass"
    confidence: float  # 0-1
    edge: float  # Expected edge vs market
    reasoning: List[str]
    key_factors: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: str = ""


@dataclass
class CouncilDecision:
    """Final decision from the council."""
    game_id: str
    pick: str
    confidence: float
    consensus_pct: float
    tier: str
    edge: float
    reasoning: str
    dissenting_views: List[str]
    member_votes: Dict[str, PickAnalysis]
    chairman_summary: str
    timestamp: datetime = field(default_factory=datetime.now)


class BaseLLMClient(ABC):
    """Base class for LLM API clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=60.0)
    
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a response from the LLM."""
        pass
    
    async def close(self):
        await self.client.aclose()


class OpenAIClient(BaseLLMClient):
    """OpenAI API client (GPT-4, etc.)."""
    
    async def generate(self, prompt: str, system: str = "") -> str:
        url = self.config.base_url or "https://api.openai.com/v1/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class AnthropicClient(BaseLLMClient):
    """Anthropic API client (Claude)."""
    
    async def generate(self, prompt: str, system: str = "") -> str:
        url = "https://api.anthropic.com/v1/messages"
        
        response = await self.client.post(
            url,
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


class GrokClient(BaseLLMClient):
    """Grok (X.AI) API client."""
    
    async def generate(self, prompt: str, system: str = "") -> str:
        url = "https://api.x.ai/v1/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model or "grok-beta",
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class GoogleClient(BaseLLMClient):
    """Google Gemini API client."""
    
    async def generate(self, prompt: str, system: str = "") -> str:
        model = self.config.model or "gemini-pro"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        response = await self.client.post(
            url,
            params={"key": self.config.api_key},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens
                }
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class PerplexityClient(BaseLLMClient):
    """Perplexity API client (with web search)."""
    
    async def generate(self, prompt: str, system: str = "") -> str:
        url = "https://api.perplexity.ai/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model or "llama-3.1-sonar-large-128k-online",
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def get_llm_client(config: LLMConfig) -> BaseLLMClient:
    """Factory function to get the appropriate LLM client."""
    clients = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.GROK: GrokClient,
        LLMProvider.GOOGLE: GoogleClient,
        LLMProvider.PERPLEXITY: PerplexityClient,
    }
    
    client_class = clients.get(config.provider)
    if not client_class:
        raise ValueError(f"Unknown provider: {config.provider}")
    
    return client_class(config)


class LLMCouncil:
    """
    Multi-model consensus system for betting decisions.
    
    Flow:
    1. Each member independently analyzes a game
    2. Members cross-review each other's analysis (anonymized)
    3. Weighted voting based on confidence and recent accuracy
    4. Chairman synthesizes final decision
    """
    
    def __init__(self, council_id: str = "main_council"):
        self.council_id = council_id
        self.members: Dict[str, CouncilMember] = {}
        self.clients: Dict[str, BaseLLMClient] = {}
        self.chairman_id: Optional[str] = None
        self.decision_history: List[CouncilDecision] = []
        
        # Load API keys from environment
        self._load_members_from_env()
    
    def _load_members_from_env(self):
        """Load council members from environment variables."""
        # OpenAI (GPT-4)
        if os.getenv("OPENAI_API_KEY"):
            self.add_member(CouncilMember(
                member_id="gpt4_analyst",
                config=LLMConfig(
                    provider=LLMProvider.OPENAI,
                    model="gpt-4-turbo-preview",
                    api_key=os.getenv("OPENAI_API_KEY")
                ),
                specialty="statistical",
                weight=1.2
            ))
        
        # Anthropic (Claude)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.add_member(CouncilMember(
                member_id="claude_analyst",
                config=LLMConfig(
                    provider=LLMProvider.ANTHROPIC,
                    model="claude-3-5-sonnet-20241022",
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                ),
                specialty="situational",
                weight=1.2
            ))
            # Claude as chairman by default (best reasoning)
            self.chairman_id = "claude_analyst"
        
        # Grok (X.AI)
        if os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"):
            self.add_member(CouncilMember(
                member_id="grok_analyst",
                config=LLMConfig(
                    provider=LLMProvider.GROK,
                    model="grok-beta",
                    api_key=os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
                ),
                specialty="contrarian",
                weight=1.0
            ))
        
        # Google (Gemini)
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            self.add_member(CouncilMember(
                member_id="gemini_analyst",
                config=LLMConfig(
                    provider=LLMProvider.GOOGLE,
                    model="gemini-1.5-pro",
                    api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                ),
                specialty="general",
                weight=1.0
            ))
        
        # Perplexity (with web search for news/injuries)
        if os.getenv("PERPLEXITY_API_KEY"):
            self.add_member(CouncilMember(
                member_id="perplexity_analyst",
                config=LLMConfig(
                    provider=LLMProvider.PERPLEXITY,
                    model="llama-3.1-sonar-large-128k-online",
                    api_key=os.getenv("PERPLEXITY_API_KEY")
                ),
                specialty="news_aware",
                weight=1.1
            ))
        
        logger.info(f"LLM Council initialized with {len(self.members)} members")
    
    def add_member(self, member: CouncilMember):
        """Add a member to the council."""
        if not member.config.is_valid:
            logger.warning(f"Invalid config for member {member.member_id}")
            return
        
        self.members[member.member_id] = member
        self.clients[member.member_id] = get_llm_client(member.config)
        logger.info(f"Added council member: {member.member_id} ({member.config.provider.value})")
    
    def _build_analysis_prompt(self, game_data: Dict) -> str:
        """Build the prompt for game analysis."""
        return f"""Analyze this NFL game for betting value:

GAME INFORMATION:
- Home Team: {game_data.get('home_team', 'Unknown')}
- Away Team: {game_data.get('away_team', 'Unknown')}
- Date/Time: {game_data.get('game_time', 'Unknown')}
- Venue: {game_data.get('venue', 'Unknown')}

CURRENT ODDS:
- Moneyline Home: {game_data.get('ml_home', 'N/A')}
- Moneyline Away: {game_data.get('ml_away', 'N/A')}
- Spread: {game_data.get('spread', 'N/A')} (Home)
- Total: {game_data.get('total', 'N/A')}

TEAM STATISTICS:
Home Team:
{json.dumps(game_data.get('home_stats', {}), indent=2)}

Away Team:
{json.dumps(game_data.get('away_stats', {}), indent=2)}

WEATHER (if outdoor):
{json.dumps(game_data.get('weather', {}), indent=2)}

INJURIES:
{json.dumps(game_data.get('injuries', []), indent=2)}

Provide your analysis in JSON format:
{{
    "pick": "home" | "away" | "over" | "under" | "pass",
    "bet_type": "moneyline" | "spread" | "total",
    "confidence": 0.0-1.0,
    "edge": estimated edge vs market (e.g., 0.05 for 5%),
    "reasoning": ["reason1", "reason2", ...],
    "key_factors": {{"factor": "impact"}},
    "risk_level": "low" | "medium" | "high"
}}

Be CONSERVATIVE. Only recommend picks with genuine edge. If uncertain, pick "pass".
"""
    
    def _build_system_prompt(self, specialty: str) -> str:
        """Build specialty-specific system prompts."""
        base = "You are an expert NFL betting analyst. Be precise, data-driven, and conservative."
        
        specialties = {
            "statistical": f"{base} Focus on advanced metrics (EPA, DVOA, success rate). Weight recent performance heavily.",
            "situational": f"{base} Focus on situational factors: rest, travel, divisional games, primetime, weather.",
            "contrarian": f"{base} Look for market inefficiencies. Challenge consensus views. Identify overreactions.",
            "news_aware": f"{base} Incorporate latest news, injuries, and public sentiment. Look for information edges.",
            "general": base
        }
        
        return specialties.get(specialty, base)
    
    async def _get_member_analysis(
        self, 
        member: CouncilMember, 
        game_data: Dict
    ) -> Optional[PickAnalysis]:
        """Get analysis from a single council member."""
        try:
            client = self.clients.get(member.member_id)
            if not client:
                return None
            
            prompt = self._build_analysis_prompt(game_data)
            system = self._build_system_prompt(member.specialty)
            
            response = await client.generate(prompt, system)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                
                return PickAnalysis(
                    member_id=member.member_id,
                    pick=analysis_data.get("pick", "pass"),
                    confidence=float(analysis_data.get("confidence", 0.5)),
                    edge=float(analysis_data.get("edge", 0.0)),
                    reasoning=analysis_data.get("reasoning", []),
                    key_factors=analysis_data.get("key_factors", {}),
                    raw_response=response
                )
            
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from {member.member_id}: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting analysis from {member.member_id}: {e}")
            return None
    
    async def analyze_game(self, game_data: Dict) -> CouncilDecision:
        """
        Full council analysis of a game.
        
        Args:
            game_data: Dict with game info, odds, stats, etc.
        
        Returns:
            CouncilDecision with consensus pick and reasoning
        """
        if not self.members:
            logger.error("No council members available!")
            return CouncilDecision(
                game_id=game_data.get("game_id", "unknown"),
                pick="pass",
                confidence=0.0,
                consensus_pct=0.0,
                tier="no_bet",
                edge=0.0,
                reasoning="No LLM council members configured",
                dissenting_views=[],
                member_votes={},
                chairman_summary="Configure API keys to enable LLM analysis"
            )
        
        # Phase 1: Independent analysis from each member
        logger.info(f"Phase 1: Getting analysis from {len(self.members)} members...")
        
        tasks = [
            self._get_member_analysis(member, game_data)
            for member in self.members.values()
        ]
        analyses = await asyncio.gather(*tasks)
        
        # Filter out None results
        valid_analyses = [a for a in analyses if a is not None]
        
        if not valid_analyses:
            return CouncilDecision(
                game_id=game_data.get("game_id", "unknown"),
                pick="pass",
                confidence=0.0,
                consensus_pct=0.0,
                tier="no_bet",
                edge=0.0,
                reasoning="All council members failed to analyze",
                dissenting_views=[],
                member_votes={},
                chairman_summary="Analysis failed"
            )
        
        # Phase 2: Weighted voting
        logger.info("Phase 2: Weighted voting...")
        
        vote_counts: Dict[str, float] = {}
        vote_confidence: Dict[str, List[float]] = {}
        vote_edge: Dict[str, List[float]] = {}
        
        for analysis in valid_analyses:
            member = self.members[analysis.member_id]
            weight = member.weight * (0.5 + member.recent_accuracy)
            
            pick = analysis.pick
            if pick not in vote_counts:
                vote_counts[pick] = 0
                vote_confidence[pick] = []
                vote_edge[pick] = []
            
            vote_counts[pick] += weight
            vote_confidence[pick].append(analysis.confidence * weight)
            vote_edge[pick].append(analysis.edge)
        
        # Find winning pick
        total_weight = sum(vote_counts.values())
        winning_pick = max(vote_counts.items(), key=lambda x: x[1])
        
        consensus_pct = winning_pick[1] / total_weight if total_weight > 0 else 0
        
        # Calculate average confidence and edge for winning pick
        avg_confidence = sum(vote_confidence[winning_pick[0]]) / len(vote_confidence[winning_pick[0]]) if vote_confidence[winning_pick[0]] else 0
        avg_edge = sum(vote_edge[winning_pick[0]]) / len(vote_edge[winning_pick[0]]) if vote_edge[winning_pick[0]] else 0
        
        # Collect reasoning and dissenting views
        winning_reasoning = []
        dissenting_views = []
        
        for analysis in valid_analyses:
            if analysis.pick == winning_pick[0]:
                winning_reasoning.extend(analysis.reasoning[:2])  # Top 2 reasons
            else:
                dissenting_views.append(f"{analysis.member_id}: {analysis.pick} ({analysis.reasoning[0] if analysis.reasoning else 'No reason'})")
        
        # Assign tier
        tier = self._assign_tier(consensus_pct, avg_confidence, avg_edge)
        
        # Phase 3: Chairman summary (if available)
        chairman_summary = ""
        if self.chairman_id and self.chairman_id in self.clients:
            try:
                chairman_prompt = f"""Summarize this betting analysis:

Pick: {winning_pick[0]}
Consensus: {consensus_pct:.1%}
Confidence: {avg_confidence:.1%}
Edge: {avg_edge:.1%}

Supporting reasons:
{json.dumps(winning_reasoning[:5], indent=2)}

Dissenting views:
{json.dumps(dissenting_views[:3], indent=2)}

Provide a 2-3 sentence executive summary for the bettor."""
                
                chairman_summary = await self.clients[self.chairman_id].generate(
                    chairman_prompt,
                    "You are summarizing betting analysis. Be concise and actionable."
                )
            except Exception as e:
                logger.warning(f"Chairman summary failed: {e}")
                chairman_summary = f"Council recommends {winning_pick[0]} with {consensus_pct:.0%} consensus"
        
        # Build member votes dict
        member_votes = {a.member_id: a for a in valid_analyses}
        
        return CouncilDecision(
            game_id=game_data.get("game_id", "unknown"),
            pick=winning_pick[0],
            confidence=avg_confidence,
            consensus_pct=consensus_pct,
            tier=tier,
            edge=avg_edge,
            reasoning="; ".join(winning_reasoning[:5]),
            dissenting_views=dissenting_views,
            member_votes=member_votes,
            chairman_summary=chairman_summary
        )
    
    def _assign_tier(self, consensus: float, confidence: float, edge: float) -> str:
        """Assign betting tier based on consensus and confidence."""
        if consensus >= 0.90 and confidence >= 0.70 and edge >= 0.08:
            return "S_tier"  # 5% bankroll
        elif consensus >= 0.75 and confidence >= 0.60 and edge >= 0.05:
            return "A_tier"  # 3% bankroll
        elif consensus >= 0.60 and confidence >= 0.50 and edge >= 0.03:
            return "B_tier"  # 1.5% bankroll
        else:
            return "no_bet"
    
    def update_member_accuracy(self, member_id: str, was_correct: bool):
        """Update member's accuracy after game result."""
        if member_id in self.members:
            member = self.members[member_id]
            member.total_votes += 1
            if was_correct:
                member.correct_votes += 1
            member.recent_accuracy = member.correct_votes / member.total_votes
            logger.info(f"Updated {member_id} accuracy: {member.recent_accuracy:.2%}")
    
    async def close(self):
        """Close all clients."""
        for client in self.clients.values():
            await client.close()


# Singleton instance
_council_instance: Optional[LLMCouncil] = None


def get_council() -> LLMCouncil:
    """Get or create the singleton LLM Council instance."""
    global _council_instance
    if _council_instance is None:
        _council_instance = LLMCouncil()
    return _council_instance


async def test_council():
    """Test the LLM Council with sample data."""
    council = get_council()
    
    if not council.members:
        print("No LLM providers configured. Set API keys:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GROK_API_KEY / XAI_API_KEY")
        print("  - GOOGLE_API_KEY / GEMINI_API_KEY")
        print("  - PERPLEXITY_API_KEY")
        return
    
    print(f"Council has {len(council.members)} members:")
    for member_id, member in council.members.items():
        print(f"  - {member_id}: {member.config.provider.value} ({member.specialty})")
    
    # Test with sample game
    game_data = {
        "game_id": "2024_12_KC_BUF",
        "home_team": "Buffalo Bills",
        "away_team": "Kansas City Chiefs",
        "game_time": "2024-11-24T16:25:00",
        "venue": "Highmark Stadium",
        "ml_home": -145,
        "ml_away": +125,
        "spread": -2.5,
        "total": 47.5,
        "home_stats": {
            "record": "9-2",
            "points_per_game": 28.5,
            "points_allowed": 20.1,
            "epa_per_play": 0.12,
            "home_record": "5-0"
        },
        "away_stats": {
            "record": "10-1",
            "points_per_game": 26.8,
            "points_allowed": 17.2,
            "epa_per_play": 0.08,
            "away_record": "4-1"
        },
        "weather": {
            "temperature": 35,
            "wind_speed": "15 mph",
            "conditions": "Partly Cloudy"
        }
    }
    
    print("\nAnalyzing: Chiefs @ Bills...")
    decision = await council.analyze_game(game_data)
    
    print(f"\n{'='*60}")
    print(f"COUNCIL DECISION")
    print(f"{'='*60}")
    print(f"Pick: {decision.pick.upper()}")
    print(f"Tier: {decision.tier}")
    print(f"Confidence: {decision.confidence:.1%}")
    print(f"Consensus: {decision.consensus_pct:.1%}")
    print(f"Edge: {decision.edge:.1%}")
    print(f"\nReasoning: {decision.reasoning}")
    
    if decision.dissenting_views:
        print(f"\nDissenting views:")
        for view in decision.dissenting_views:
            print(f"  - {view}")
    
    print(f"\nChairman Summary: {decision.chairman_summary}")
    
    await council.close()


if __name__ == "__main__":
    asyncio.run(test_council())

