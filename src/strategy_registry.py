"""
Strategy Registry - Track and manage discovered betting strategies

BEGINNER-FRIENDLY EXPLANATION:
This module is like a notebook where you write down all the betting patterns
you've discovered. It remembers:
- What strategies you found
- Which ones you accepted/rejected
- Performance stats for each strategy
- Notes about why you made certain decisions

Think of it as a recipe book for betting strategies!
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from enum import Enum
import re

logger = logging.getLogger(__name__)

# Project root directory (for absolute path resolution)
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "strategies" / "registry.json"


def normalize_pattern(text: str) -> str:
    """
    Normalize a pattern string for better duplicate detection.

    BEGINNER NOTE: Makes comparison more reliable by:
    - Converting to lowercase
    - Removing special characters
    - Standardizing whitespace
    - Removing common words like "v1", "v2", etc.

    Args:
        text: Raw pattern string

    Returns:
        Normalized string for comparison
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove version suffixes (v1, v2, etc.)
    text = re.sub(r"\s*\(v\d+\)|\s*v\d+$", "", text)

    # Replace special chars with spaces
    text = re.sub(r"[_\-:,\(\)]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


class StrategyStatus(Enum):
    """
    Strategy status types.

    BEGINNER NOTE: Like labels on file folders.
    - PENDING = New discovery, haven't decided yet
    - ACCEPTED = Good strategy, using it
    - REJECTED = Tested it, not profitable
    - ARCHIVED = Was good, stopped using it
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class Strategy:
    """
    A single betting strategy.

    BEGINNER NOTE: This is like a recipe card.
    It has all the info about one specific betting pattern.
    """

    strategy_id: str  # Unique ID (like "prime_time_unders_v1")
    name: str  # Human-readable name
    description: str  # What is this strategy?
    pattern: str  # The actual pattern (used for duplicate detection)

    # Performance metrics
    win_rate: float  # % of bets won
    roi: float  # Return on investment %
    sample_size: int  # How many bets tested
    edge: float  # Edge over market (%)
    sharpe_ratio: Optional[float] = None  # Risk-adjusted return

    # Metadata
    status: str = StrategyStatus.PENDING.value
    date_discovered: str = None
    date_reviewed: Optional[str] = None
    reviewer_notes: str = ""

    # Conditions (what makes this strategy trigger?)
    conditions: Dict = None

    # Version tracking
    version: int = 1
    previous_version_id: Optional[str] = None

    def __post_init__(self):
        """Auto-set date_discovered if not provided."""
        if self.date_discovered is None:
            self.date_discovered = datetime.now().isoformat()
        if self.conditions is None:
            self.conditions = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Strategy":
        """Create Strategy from dictionary."""
        return cls(**data)

    def similarity_score(self, other_pattern: str, other_name: str = None) -> float:
        """
        Calculate how similar this strategy is to another pattern/name.

        BEGINNER NOTE: Like checking if two recipes are the same.
        Returns 0.0 (completely different) to 1.0 (identical).
        Now checks BOTH pattern and name for better duplicate detection.

        Args:
            other_pattern: Pattern string to compare
            other_name: Optional name to also compare

        Returns:
            Similarity score (0.0-1.0) - highest of pattern/name matches
        """
        # Normalize both strings for comparison
        norm_self_pattern = normalize_pattern(self.pattern)
        norm_other_pattern = normalize_pattern(other_pattern)

        # Pattern similarity
        pattern_score = SequenceMatcher(
            None, norm_self_pattern, norm_other_pattern
        ).ratio()

        # Also check name similarity if provided
        if other_name:
            norm_self_name = normalize_pattern(self.name)
            norm_other_name = normalize_pattern(other_name)
            name_score = SequenceMatcher(None, norm_self_name, norm_other_name).ratio()
            # Return highest match
            return max(pattern_score, name_score)

        return pattern_score

    def is_similar_to(
        self, other_pattern: str, other_name: str = None, threshold: float = 0.85
    ) -> bool:
        """
        Check if this strategy is similar to another pattern.

        BEGINNER NOTE: Fuzzy matching!
        "Prime-time unders" and "Primetime unders" are 95% similar = DUPLICATE!
        Now also checks names, not just patterns.

        Args:
            other_pattern: Pattern to compare
            other_name: Optional name to also compare
            threshold: How similar = duplicate? (default 0.85 = 85%)

        Returns:
            True if strategies are duplicates
        """
        score = self.similarity_score(other_pattern, other_name)
        is_match = score >= threshold

        if is_match:
            logger.debug(
                f"Fuzzy match found: '{self.name}' matches '{other_name or other_pattern}' "
                f"(score: {score:.2%})"
            )

        return is_match


class StrategyRegistry:
    """
    Registry to track all betting strategies.

    BEGINNER NOTE: This is the filing cabinet that holds all your strategy cards.
    It can:
    - Add new strategies
    - Find strategies by status (accepted/rejected)
    - Check for duplicates
    - Update strategy performance
    """

    def __init__(self, registry_path: str = None):
        """
        Initialize the registry.

        Args:
            registry_path: Path to registry JSON file (defaults to project root/data/strategies/registry.json)
        """
        # Use absolute path to avoid working directory issues
        if registry_path is None:
            self.registry_path = DEFAULT_REGISTRY_PATH
        else:
            self.registry_path = Path(registry_path)

        self.strategies: Dict[str, Strategy] = {}
        self._load_registry()

    def _load_registry(self):
        """
        Load strategies from JSON file.

        BEGINNER NOTE: Like opening your notebook and reading all the strategies.
        If the file doesn't exist yet, we create an empty registry.
        """
        logger.debug(f"Loading registry from: {self.registry_path.absolute()}")

        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)

                # Convert dict data to Strategy objects
                self.strategies = {
                    strategy_id: Strategy.from_dict(strategy_data)
                    for strategy_id, strategy_data in data.items()
                }

                # Log summary by status
                stats = {}
                for strategy in self.strategies.values():
                    stats[strategy.status] = stats.get(strategy.status, 0) + 1

                logger.info(f"Loaded {len(self.strategies)} strategies from registry")
                logger.debug(f"Registry status breakdown: {stats}")

                # Log each strategy at debug level
                for sid, strategy in self.strategies.items():
                    logger.debug(f"  - {sid}: {strategy.status}")

            except Exception as e:
                logger.error(f"Error loading registry: {e}", exc_info=True)
                self.strategies = {}
        else:
            logger.info(
                f"No existing registry found at {self.registry_path}, creating new one"
            )
            self.strategies = {}
            self._save_registry()

    def _save_registry(self):
        """
        Save strategies to JSON file.

        BEGINNER NOTE: Like writing your strategies back into the notebook.
        """
        # Create directory if it doesn't exist
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Strategy objects to dicts
        data = {
            strategy_id: strategy.to_dict()
            for strategy_id, strategy in self.strategies.items()
        }

        try:
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(
                f"Saved {len(self.strategies)} strategies to {self.registry_path}"
            )
            logger.debug(f"Saved strategies: {list(self.strategies.keys())}")
        except Exception as e:
            logger.error(
                f"Error saving registry to {self.registry_path}: {e}", exc_info=True
            )

    def add_strategy(
        self, strategy: Strategy, skip_duplicate_check: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Add a new strategy to the registry.

        BEGINNER NOTE: Like adding a new recipe to your cookbook.
        But first we check: "Do I already have this recipe?"

        Args:
            strategy: Strategy to add
            skip_duplicate_check: Skip checking for duplicates (use carefully!)

        Returns:
            (success: bool, message: str)
        """
        logger.debug(
            f"add_strategy called: id={strategy.strategy_id}, "
            f"name='{strategy.name}', skip_dup={skip_duplicate_check}"
        )

        # Check for duplicates
        if not skip_duplicate_check:
            logger.debug(
                f"Checking for duplicates of: '{strategy.pattern}' / '{strategy.name}'"
            )
            duplicate = self.find_similar_strategy(strategy.pattern, strategy.name)
            if duplicate:
                logger.info(
                    f"Duplicate detected: '{strategy.name}' matches existing "
                    f"'{duplicate.name}' ({duplicate.strategy_id})"
                )
                return (
                    False,
                    f"Similar strategy already exists: {duplicate.strategy_id} ({duplicate.name})",
                )

        # Check if ID already exists
        if strategy.strategy_id in self.strategies:
            logger.warning(
                f"Strategy ID {strategy.strategy_id} already exists in registry"
            )
            return False, f"Strategy ID {strategy.strategy_id} already exists"

        # Add strategy
        self.strategies[strategy.strategy_id] = strategy
        self._save_registry()

        logger.info(f"Added new strategy: {strategy.strategy_id} - '{strategy.name}'")
        return True, f"Strategy {strategy.strategy_id} added successfully"

    def update_strategy(self, strategy_id: str, **updates) -> tuple[bool, str]:
        """
        Update an existing strategy.

        BEGINNER NOTE: Like editing a recipe card.
        You can change any field (status, notes, stats, etc.)

        Args:
            strategy_id: ID of strategy to update
            **updates: Fields to update (e.g., status="accepted", roi=25.5)

        Returns:
            (success: bool, message: str)
        """
        logger.debug(f"update_strategy called: {strategy_id} with updates: {updates}")

        if strategy_id not in self.strategies:
            logger.warning(f"Strategy {strategy_id} not found in registry")
            return False, f"Strategy {strategy_id} not found"

        strategy = self.strategies[strategy_id]
        old_status = strategy.status

        # Update fields
        for key, value in updates.items():
            if hasattr(strategy, key):
                old_value = getattr(strategy, key)
                setattr(strategy, key, value)
                logger.debug(f"  {key}: '{old_value}' -> '{value}'")
            else:
                logger.warning(f"Unknown field '{key}' for strategy")

        self._save_registry()

        if "status" in updates and updates["status"] != old_status:
            logger.info(
                f"Strategy status changed: {strategy_id} [{old_status} -> {updates['status']}]"
            )
        else:
            logger.info(f"Updated strategy: {strategy_id}")

        return True, f"Strategy {strategy_id} updated successfully"

    def accept_strategy(self, strategy_id: str, notes: str = "") -> tuple[bool, str]:
        """
        Accept a strategy (mark as ACCEPTED).

        BEGINNER NOTE: "This strategy is good, I'm going to use it!"

        Args:
            strategy_id: ID of strategy to accept
            notes: Why you accepted it

        Returns:
            (success: bool, message: str)
        """
        logger.info(
            f"ACCEPTING strategy: {strategy_id}"
            + (f" (notes: {notes})" if notes else "")
        )
        return self.update_strategy(
            strategy_id,
            status=StrategyStatus.ACCEPTED.value,
            date_reviewed=datetime.now().isoformat(),
            reviewer_notes=notes,
        )

    def reject_strategy(self, strategy_id: str, notes: str = "") -> tuple[bool, str]:
        """
        Reject a strategy (mark as REJECTED).

        BEGINNER NOTE: "This strategy doesn't work for me."

        Args:
            strategy_id: ID of strategy to reject
            notes: Why you rejected it

        Returns:
            (success: bool, message: str)
        """
        logger.info(
            f"REJECTING strategy: {strategy_id}"
            + (f" (notes: {notes})" if notes else "")
        )
        return self.update_strategy(
            strategy_id,
            status=StrategyStatus.REJECTED.value,
            date_reviewed=datetime.now().isoformat(),
            reviewer_notes=notes,
        )

    def archive_strategy(self, strategy_id: str, notes: str = "") -> tuple[bool, str]:
        """
        Archive a strategy (was good, stopped using it).

        BEGINNER NOTE: "This used to work, but not anymore."

        Args:
            strategy_id: ID of strategy to archive
            notes: Why you archived it

        Returns:
            (success: bool, message: str)
        """
        return self.update_strategy(
            strategy_id,
            status=StrategyStatus.ARCHIVED.value,
            date_reviewed=datetime.now().isoformat(),
            reviewer_notes=notes,
        )

    def get_strategies_by_status(self, status: StrategyStatus) -> List[Strategy]:
        """
        Get all strategies with a specific status.

        BEGINNER NOTE: Like pulling out all the "accepted" recipe cards from your box.

        Args:
            status: Status to filter by

        Returns:
            List of strategies with that status
        """
        return [
            strategy
            for strategy in self.strategies.values()
            if strategy.status == status.value
        ]

    def get_pending_strategies(self) -> List[Strategy]:
        """Get all pending strategies (need review)."""
        return self.get_strategies_by_status(StrategyStatus.PENDING)

    def get_accepted_strategies(self) -> List[Strategy]:
        """Get all accepted strategies (currently using)."""
        return self.get_strategies_by_status(StrategyStatus.ACCEPTED)

    def get_rejected_strategies(self) -> List[Strategy]:
        """Get all rejected strategies (tested, didn't work)."""
        return self.get_strategies_by_status(StrategyStatus.REJECTED)

    def find_similar_strategy(
        self, pattern: str, name: str = None, threshold: float = 0.85
    ) -> Optional[Strategy]:
        """
        Find if a similar strategy already exists.

        BEGINNER NOTE: Duplicate detection!
        Checks if "Prime-time unders" already exists before adding "Primetime unders"
        Now also checks strategy names, not just patterns.

        Args:
            pattern: Pattern string to search for
            name: Optional strategy name to also check
            threshold: Similarity threshold (0.85 = 85% similar = duplicate)

        Returns:
            Existing similar strategy, or None if not found
        """
        best_match = None
        best_score = 0

        for strategy in self.strategies.values():
            score = strategy.similarity_score(pattern, name)

            if score >= threshold and score > best_score:
                best_match = strategy
                best_score = score

                logger.debug(
                    f"Duplicate detection: '{name or pattern}' matches "
                    f"'{strategy.name}' (score: {score:.2%})"
                )

        if best_match:
            logger.info(
                f"Found similar strategy: '{name or pattern}' -> '{best_match.name}' "
                f"(similarity: {best_score:.2%})"
            )

        return best_match

    def check_for_updates(self, pattern: str, new_metrics: Dict) -> Optional[Dict]:
        """
        Check if a strategy has improved stats (version update).

        BEGINNER NOTE: "Hey! This strategy's win rate went from 60% to 65%!"

        Args:
            pattern: Strategy pattern
            new_metrics: New performance metrics (win_rate, roi, etc.)

        Returns:
            Dict with old_metrics, new_metrics, improvement if found, None otherwise
        """
        similar = self.find_similar_strategy(pattern)

        if not similar:
            return None

        # Compare metrics
        old_metrics = {
            "win_rate": similar.win_rate,
            "roi": similar.roi,
            "sample_size": similar.sample_size,
            "edge": similar.edge,
        }

        # Calculate improvements
        improvements = {}
        for key in ["win_rate", "roi", "edge"]:
            if key in new_metrics:
                old_val = old_metrics[key]
                new_val = new_metrics[key]
                if new_val > old_val:
                    improvements[key] = {
                        "old": old_val,
                        "new": new_val,
                        "change": new_val - old_val,
                        "pct_change": (
                            ((new_val - old_val) / abs(old_val) * 100)
                            if old_val != 0
                            else 0
                        ),
                    }

        if improvements:
            return {
                "strategy_id": similar.strategy_id,
                "strategy_name": similar.name,
                "old_metrics": old_metrics,
                "new_metrics": new_metrics,
                "improvements": improvements,
            }

        return None

    def create_strategy_version(
        self, original_id: str, updated_metrics: Dict
    ) -> tuple[bool, str]:
        """
        Create a new version of an existing strategy.

        BEGINNER NOTE: Like updating a recipe with better instructions.
        We keep the old version (v1) and create a new one (v2).

        Args:
            original_id: ID of original strategy
            updated_metrics: New performance metrics

        Returns:
            (success: bool, message: str)
        """
        if original_id not in self.strategies:
            return False, f"Original strategy {original_id} not found"

        original = self.strategies[original_id]

        # Create new version
        new_version = original.version + 1
        new_id = f"{original.strategy_id.rsplit('_v', 1)[0]}_v{new_version}"

        # Clone strategy with updated metrics
        new_strategy = Strategy(
            strategy_id=new_id,
            name=f"{original.name} (v{new_version})",
            description=original.description,
            pattern=original.pattern,
            win_rate=updated_metrics.get("win_rate", original.win_rate),
            roi=updated_metrics.get("roi", original.roi),
            sample_size=updated_metrics.get("sample_size", original.sample_size),
            edge=updated_metrics.get("edge", original.edge),
            sharpe_ratio=updated_metrics.get("sharpe_ratio", original.sharpe_ratio),
            status=StrategyStatus.PENDING.value,  # Needs re-review
            conditions=original.conditions.copy(),
            version=new_version,
            previous_version_id=original_id,
        )

        # Add new version
        success, message = self.add_strategy(new_strategy, skip_duplicate_check=True)

        if success:
            # Archive old version
            self.archive_strategy(original_id, f"Superseded by {new_id}")

        return success, message

    def get_all_strategies(self) -> List[Strategy]:
        """Get all strategies (all statuses)."""
        return list(self.strategies.values())

    def delete_strategy(self, strategy_id: str) -> tuple[bool, str]:
        """
        Delete a strategy permanently.

        BEGINNER NOTE: Like ripping out a recipe page.
        USE WITH CAUTION! Usually you want to archive instead.

        Args:
            strategy_id: ID of strategy to delete

        Returns:
            (success: bool, message: str)
        """
        if strategy_id not in self.strategies:
            return False, f"Strategy {strategy_id} not found"

        del self.strategies[strategy_id]
        self._save_registry()

        logger.info(f"Deleted strategy: {strategy_id}")
        return True, f"Strategy {strategy_id} deleted"

    def get_stats(self) -> Dict:
        """
        Get summary statistics about the registry.

        BEGINNER NOTE: Overview of your strategy collection.

        Returns:
            Dict with total, pending, accepted, rejected, archived counts
        """
        return {
            "total": len(self.strategies),
            "pending": len(self.get_pending_strategies()),
            "accepted": len(self.get_accepted_strategies()),
            "rejected": len(self.get_rejected_strategies()),
            "archived": len(self.get_strategies_by_status(StrategyStatus.ARCHIVED)),
        }
