#!/usr/bin/env python3
"""
NFL Edge Finder - AI Reasoning Swarm
====================================
Multi-AI consensus reasoning for bet recommendations.
Uses OpenAI, Anthropic, and Google AI for intelligent analysis.

SECURITY: Refuses all codebase/system questions.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

# Load environment variables
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / "api_keys.env")

# =============================================================================
# SECURITY GUARDRAILS
# =============================================================================

FORBIDDEN_TOPICS = [
    "code",
    "codebase",
    "source",
    "database",
    "api key",
    "password",
    "authentication",
    "admin",
    "system",
    "security",
    "vulnerability",
    "sql",
    "query",
    "backend",
    "implementation",
    "algorithm details",
    "model architecture",
    "training data",
    "file structure",
    "config",
]


def is_safe_query(query: str) -> bool:
    """Check if query is safe (not asking about system internals)."""
    query_lower = query.lower()

    for forbidden in FORBIDDEN_TOPICS:
        if forbidden in query_lower:
            return False

    return True


def get_security_refusal() -> str:
    """Return security refusal message."""
    return """
🔒 **Security Notice**

I can't answer questions about:
- System code or implementation
- Database structure or queries  
- API keys or authentication
- Security configurations
- Model architecture details

**What I CAN help with:**
- Betting strategy and recommendations
- Game analysis and predictions
- Risk management advice
- Bankroll optimization
- NFL team/player analysis

Please ask about betting strategy instead! 🏈
"""


# =============================================================================
# AI PROVIDER INTEGRATIONS
# =============================================================================


class OpenAIReasoner:
    """OpenAI GPT-4 reasoning."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.available = bool(self.api_key)

    def analyze_bet(self, game_info: Dict, bet_info: Dict) -> Optional[str]:
        """Analyze bet using GPT-4."""
        if not self.available:
            return None

        try:
            import openai

            openai.api_key = self.api_key

            prompt = f"""Analyze this NFL bet as a professional sports bettor:

Game: {game_info['matchup']}
Bet: {bet_info['bet_type']}
Odds: {bet_info['odds']}
Model Win Probability: {bet_info['win_prob']}%
Edge: {bet_info['edge']}%

Context:
{game_info.get('context', '')}

Provide a concise 2-3 sentence analysis focusing on:
1. Key factors supporting this bet
2. Main risks to consider
3. Your confidence level (High/Medium/Low)

Be direct and actionable. Focus on football analysis only."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert NFL betting analyst. Provide clear, actionable insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"OpenAI Error: {str(e)[:50]}"


class AnthropicReasoner:
    """Anthropic Claude reasoning."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.available = bool(self.api_key)

    def analyze_bet(self, game_info: Dict, bet_info: Dict) -> Optional[str]:
        """Analyze bet using Claude."""
        if not self.available:
            return None

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = f"""Analyze this NFL betting opportunity:

{game_info['matchup']}
Bet: {bet_info['bet_type']} @ {bet_info['odds']}
Win Prob: {bet_info['win_prob']}% | Edge: +{bet_info['edge']}%

{game_info.get('context', '')}

Provide 2-3 sentences analyzing:
1. Strategic value of this bet
2. Key risk factors
3. Overall assessment

Focus on actionable football insights."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text.strip()

        except Exception as e:
            return f"Claude Error: {str(e)[:50]}"


class GoogleReasoner:
    """Google Gemini reasoning."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.available = bool(self.api_key)

    def analyze_bet(self, game_info: Dict, bet_info: Dict) -> Optional[str]:
        """Analyze bet using Gemini Pro."""
        if not self.available:
            return None

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-pro")

            prompt = f"""NFL Betting Analysis:

Game: {game_info['matchup']}
Recommended Bet: {bet_info['bet_type']}
Odds: {bet_info['odds']}
Win Probability: {bet_info['win_prob']}%
Expected Value: +{bet_info['edge']}%

Game Context:
{game_info.get('context', '')}

Analyze this bet in 2-3 clear sentences covering:
- Why this bet has value
- Primary concerns
- Confidence rating

Be concise and football-focused."""

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            return f"Gemini Error: {str(e)[:50]}"


# =============================================================================
# REASONING SWARM
# =============================================================================


class AIReasoningSwarm:
    """Multi-AI reasoning system with consensus analysis."""

    def __init__(self):
        self.openai = OpenAIReasoner()
        self.anthropic = AnthropicReasoner()
        self.google = GoogleReasoner()

        self.reasoners = {
            "GPT-4": self.openai,
            "Claude": self.anthropic,
            "Gemini": self.google,
        }

    def get_available_ais(self) -> List[str]:
        """Get list of available AI reasoners."""
        return [name for name, reasoner in self.reasoners.items() if reasoner.available]

    def analyze_bet_swarm(self, game_info: Dict, bet_info: Dict) -> Dict[str, str]:
        """Get analysis from all available AIs."""
        results = {}

        for name, reasoner in self.reasoners.items():
            if reasoner.available:
                analysis = reasoner.analyze_bet(game_info, bet_info)
                if analysis:
                    results[name] = analysis

        return results

    def get_consensus_view(self, swarm_results: Dict[str, str]) -> str:
        """Synthesize consensus from multiple AI views."""
        if not swarm_results:
            return "No AI analysis available. Configure API keys in settings."

        num_ais = len(swarm_results)

        # Simple consensus based on sentiment
        positive_keywords = [
            "strong",
            "good",
            "solid",
            "favorable",
            "confident",
            "value",
        ]
        negative_keywords = [
            "risky",
            "concern",
            "weak",
            "cautious",
            "avoid",
            "questionable",
        ]

        positive_count = 0
        negative_count = 0

        for analysis in swarm_results.values():
            analysis_lower = analysis.lower()
            positive_count += sum(1 for kw in positive_keywords if kw in analysis_lower)
            negative_count += sum(1 for kw in negative_keywords if kw in analysis_lower)

        if positive_count > negative_count * 1.5:
            consensus = "✅ **STRONG CONSENSUS**: AIs agree this bet has solid value."
        elif negative_count > positive_count * 1.5:
            consensus = "⚠️ **CAUTION**: Multiple AIs flag concerns with this bet."
        else:
            consensus = (
                "🤔 **MIXED SIGNALS**: AIs have differing views. Use your judgment."
            )

        return consensus

    def answer_betting_question(self, question: str, context: Dict = None) -> str:
        """Answer general betting questions (with security checks)."""
        # Security check
        if not is_safe_query(question):
            return get_security_refusal()

        # Use first available AI
        for name, reasoner in self.reasoners.items():
            if reasoner.available:
                try:
                    if name == "GPT-4":
                        import openai

                        openai.api_key = reasoner.api_key

                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert NFL betting analyst. Answer questions about betting strategy, game analysis, and risk management. NEVER discuss system internals, code, or security.",
                                },
                                {"role": "user", "content": question},
                            ],
                            max_tokens=300,
                            temperature=0.7,
                        )

                        return response.choices[0].message.content.strip()

                    elif name == "Claude":
                        import anthropic

                        client = anthropic.Anthropic(api_key=reasoner.api_key)

                        message = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=300,
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"As an NFL betting expert, answer this question (refuse if about system/code): {question}",
                                }
                            ],
                        )

                        return message.content[0].text.strip()

                    elif name == "Gemini":
                        import google.generativeai as genai

                        genai.configure(api_key=reasoner.api_key)
                        model = genai.GenerativeModel("gemini-pro")

                        response = model.generate_content(
                            f"Answer this NFL betting question: {question}"
                        )
                        return response.text.strip()

                except Exception as e:
                    continue

        return "⚠️ No AI providers configured. Add API keys in Admin Panel → System settings."


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================


def show_ai_reasoning_widget(game_info: Dict, bet_info: Dict):
    """Display AI reasoning swarm widget."""
    swarm = AIReasoningSwarm()

    available_ais = swarm.get_available_ais()

    if not available_ais:
        st.info(
            "💡 **Enable AI Reasoning**: Add OpenAI, Anthropic, or Google API keys in Admin Panel for intelligent bet analysis!"
        )
        return

    st.markdown("### 🤖 AI Reasoning Swarm")
    st.caption(f"Multi-AI analysis from: {', '.join(available_ais)}")

    with st.spinner("🧠 Consulting AI swarm..."):
        swarm_results = swarm.analyze_bet_swarm(game_info, bet_info)

    if swarm_results:
        # Show consensus
        consensus = swarm.get_consensus_view(swarm_results)
        st.markdown(consensus)

        st.divider()

        # Show individual AI analyses
        tabs = st.tabs(list(swarm_results.keys()))

        for tab, (ai_name, analysis) in zip(tabs, swarm_results.items()):
            with tab:
                icon = {"GPT-4": "🟢", "Claude": "🟣", "Gemini": "🔵"}[ai_name]
                st.markdown(f"{icon} **{ai_name} Analysis:**")
                st.write(analysis)


def show_ai_chat_assistant():
    """Show AI chat assistant for betting questions."""
    st.markdown("### 💬 AI Betting Assistant")
    st.caption(
        "Ask questions about betting strategy, game analysis, or risk management"
    )

    swarm = AIReasoningSwarm()
    available_ais = swarm.get_available_ais()

    if not available_ais:
        st.warning("⚠️ No AI providers configured. Add API keys to enable chat.")
        return

    # Initialize chat history
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Display chat history
    for message in st.session_state.ai_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if question := st.chat_input("Ask me anything about NFL betting..."):
        # Add user message
        st.session_state.ai_chat_history.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = swarm.answer_betting_question(question)
            st.markdown(response)

        # Add assistant message
        st.session_state.ai_chat_history.append(
            {"role": "assistant", "content": response}
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "AIReasoningSwarm",
    "show_ai_reasoning_widget",
    "show_ai_chat_assistant",
    "is_safe_query",
    "get_security_refusal",
]
