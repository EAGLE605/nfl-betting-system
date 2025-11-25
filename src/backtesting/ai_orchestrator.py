"""AI Orchestrator for Backtesting - Orchestrates self-improving backtesting cycles."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.base_agent import BaseAgent
from src.backtesting.data_loader import BacktestDataLoader
from src.backtesting.engine import BacktestEngine
from src.backtesting.prediction_generator import PredictionGenerator
from src.swarms.strategy_generation_swarm import StrategyGenerationSwarm
from src.swarms.validation_swarm import ValidationSwarm

logger = logging.getLogger(__name__)


class AIBacktestOrchestrator:
    """
    AI Orchestrator for Backtesting

    Makes 5 key decisions:
    1. Generate new vs evolve existing strategies
    2. How many strategies to test
    3. Which data period to focus on
    4. Human-in-the-loop flagging
    5. Deploy to production
    """

    def __init__(
        self, strategy_agents: List[BaseAgent], validation_agents: List[BaseAgent]
    ):
        """
        Initialize AI backtest orchestrator.

        Args:
            strategy_agents: Agents for strategy generation
            validation_agents: Agents for validation
        """
        self.strategy_swarm = StrategyGenerationSwarm(strategy_agents)
        self.validation_swarm = ValidationSwarm(validation_agents)
        self.backtest_engine = BacktestEngine()
        self.data_loader = BacktestDataLoader()
        self.prediction_generator = PredictionGenerator()

        self.strategies_tested = 0
        self.strategies_deployed = 0
        self.cycle_count = 0

        logger.info("AI Backtest Orchestrator initialized")

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run one complete backtesting cycle.

        Returns:
            Cycle results
        """
        self.cycle_count += 1
        logger.info(f"Starting backtesting cycle {self.cycle_count}")

        # Decision 1: Generate new vs evolve existing
        decision = await self._decide_generation_strategy()

        if decision == "generate_new":
            # Phase 1: Strategy Generation (Swarm - 10 agents)
            strategies = await self.strategy_swarm.generate_strategies()
        else:
            # Evolve existing strategies
            strategies = await self._evolve_strategies()

        # Decision 2: How many strategies to test
        test_count = await self._decide_test_count(strategies)
        strategies_to_test = strategies[:test_count]

        # Decision 3: Which data period to focus on
        data_period = await self._decide_data_period()

        # Phase 2: Backtesting (Walk-Forward Engine - no forward knowledge)
        backtest_results = []
        for strategy in strategies_to_test:
            result = await self._run_backtest(strategy, data_period)
            backtest_results.append(result)
            self.strategies_tested += 1

        # Phase 3: Validation (Swarm - 5 agents, unanimous approval)
        validated_strategies = []
        for strategy, result in zip(strategies_to_test, backtest_results):
            strategy["backtest_result"] = result
            validation = await self.validation_swarm.validate_strategy(strategy)

            if validation.get("validated"):
                validated_strategies.append(strategy)

        # Phase 4: Analysis & Learning
        analysis = await self._analyze_results(validated_strategies)

        # Phase 5: Strategy Evolution
        evolved = await self._evolve_strategies(validated_strategies)

        # Decision 5: Deploy to production
        deployed = await self._decide_deployment(validated_strategies)
        self.strategies_deployed += len(deployed)

        return {
            "cycle": self.cycle_count,
            "strategies_generated": len(strategies),
            "strategies_tested": len(strategies_to_test),
            "strategies_validated": len(validated_strategies),
            "strategies_deployed": len(deployed),
            "analysis": analysis,
        }

    async def _decide_generation_strategy(self) -> str:
        """Decision 1: Generate new vs evolve existing."""
        # Simple logic: alternate between new and evolution
        if self.cycle_count % 2 == 0:
            return "generate_new"
        return "evolve_existing"

    async def _decide_test_count(self, strategies: List[Dict]) -> int:
        """Decision 2: How many strategies to test."""
        # Test top 5 strategies
        return min(5, len(strategies))

    async def _decide_data_period(self) -> Dict[str, Any]:
        """Decision 3: Which data period to focus on."""
        # Focus on recent data (last 2 seasons)
        current_year = datetime.now().year
        return {
            "start_year": current_year - 2,
            "end_year": current_year - 1,
            "focus": "recent",
        }

    async def _run_backtest(
        self, strategy: Dict[str, Any], data_period: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy using real historical data.

        Args:
            strategy: Strategy config with model_name and parameters
            data_period: Period config with start_year, end_year, focus

        Returns:
            Dict with backtest metrics (ROI, win_rate, sharpe, etc.)
        """
        logger.info(f"Backtesting strategy: {strategy.get('id')}")

        try:
            # Load historical data
            schedules_df, pbp_df = self.data_loader.get_backtest_data(data_period)

            # Generate predictions using model
            predictions_df = self.prediction_generator.generate_predictions(
                schedules_df, strategy, pbp_df
            )

            if len(predictions_df) == 0:
                logger.warning("No predictions generated, returning poor metrics")
                return {
                    "roi": -0.10,
                    "win_rate": 0.45,
                    "sharpe_ratio": -0.5,
                    "max_drawdown": 0.25,
                    "total_bets": 0,
                    "error": "No predictions generated",
                }

            # Run backtest
            metrics, history_df = self.backtest_engine.run_backtest(predictions_df)

            logger.info(
                f"Backtest complete: ROI={metrics['roi']:.2%}, "
                f"Win Rate={metrics['win_rate']:.2%}, "
                f"Sharpe={metrics.get('sharpe_ratio', 0):.2f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            # Return poor metrics on failure
            return {
                "roi": -0.20,
                "win_rate": 0.40,
                "sharpe_ratio": -1.0,
                "max_drawdown": 0.30,
                "total_bets": 0,
                "error": str(e),
            }

    async def _analyze_results(self, strategies: List[Dict]) -> Dict[str, Any]:
        """Phase 4: Analysis & Learning."""
        if not strategies:
            return {"insights": []}

        avg_roi = sum(
            s.get("backtest_result", {}).get("roi", 0) for s in strategies
        ) / len(strategies)
        avg_win_rate = sum(
            s.get("backtest_result", {}).get("win_rate", 0) for s in strategies
        ) / len(strategies)

        return {
            "avg_roi": avg_roi,
            "avg_win_rate": avg_win_rate,
            "insights": ["Strategies performing well", "Consider increasing bet sizes"],
        }

    async def _evolve_strategies(
        self, existing: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Evolve existing strategies."""
        if existing is None:
            existing = []

        # Evolution logic: mutate parameters, combine winners
        evolved = []
        for strategy in existing:
            # Mutate strategy
            evolved_strategy = strategy.copy()
            evolved_strategy["id"] = f"{strategy['id']}_evolved"
            evolved_strategy["evolved_from"] = strategy["id"]
            evolved.append(evolved_strategy)

        return evolved

    async def _decide_deployment(self, strategies: List[Dict]) -> List[Dict]:
        """Decision 5: Deploy to production."""
        # Deploy strategies with ROI > 10% and win_rate > 55%
        deployed = []
        for strategy in strategies:
            result = strategy.get("backtest_result", {})
            if result.get("roi", 0) > 0.10 and result.get("win_rate", 0) > 0.55:
                deployed.append(strategy)
                logger.info(f"Deploying strategy: {strategy.get('id')}")

        return deployed

    async def run_continuous(self, interval: int = 3600):
        """Run continuous backtesting cycles."""
        logger.info("Starting continuous backtesting cycles")

        while True:
            try:
                result = await self.run_cycle()
                logger.info(
                    f"Cycle {result['cycle']} complete: {result['strategies_deployed']} strategies deployed"
                )
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Backtesting cycle error: {e}")
                await asyncio.sleep(60)
