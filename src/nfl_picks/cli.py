"""Command-line interface for NFL Picks."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import settings
from .core import Pick, PickSignal, Predictor


def display_picks(picks: list[Pick]) -> None:
    """Display picks in simple, readable format."""
    strong = [p for p in picks if p.signal == PickSignal.STRONG]
    lean = [p for p in picks if p.signal == PickSignal.LEAN]
    skip = [p for p in picks if p.signal == PickSignal.SKIP]

    if strong:
        print("\n" + "=" * 55)
        print("🟢 STRONG PICKS")
        print("=" * 55)
        for p in strong:
            print(f"\n  {p.pick_display}")
            print(f"  {p.matchup}")
            print(f"  Confidence: {p.confidence}%")
            print()
            print("  Why this hits:")
            for reason in p.reasons:
                print(f"    ✓ {reason}")

            if settings.calculated_unit_size:
                unit = settings.calculated_unit_size
                suggested = unit * (1 + (p.confidence - 62) / 20)  # Scale with confidence
                print(f"\n  Suggested: ${suggested:.0f}")

    if lean:
        print("\n" + "-" * 55)
        print("🟡 LEAN")
        print("-" * 55)
        for p in lean:
            print(f"  {p.pick_display} ({p.confidence}%) - {p.matchup}")

    if skip:
        print(f"\n⚫ SKIP: {len(skip)} games below {settings.confidence_threshold*100:.0f}% threshold")

    total_strong = len(strong)
    total_lean = len(lean)
    print(f"\n{'=' * 55}")
    print(f"SUMMARY: {total_strong} strong, {total_lean} lean, {len(skip)} skip")
    print(f"{'=' * 55}\n")


def save_picks(picks: list[Pick]) -> None:
    """Save picks to history file."""
    history: list[dict] = []
    if settings.picks_file.exists():
        with open(settings.picks_file) as f:
            history = json.load(f)

    for p in picks:
        # Don't duplicate
        existing_ids = {h["game_id"] for h in history}
        if p.game_id not in existing_ids:
            history.append(p.to_dict())

    with open(settings.picks_file, "w") as f:
        json.dump(history, f, indent=2)

    print(f"Saved {len(picks)} picks to {settings.picks_file}")


def show_history() -> None:
    """Display pick history and stats."""
    if not settings.picks_file.exists():
        print("No history yet")
        return

    with open(settings.picks_file) as f:
        history = json.load(f)

    picks = [Pick.from_dict(h) for h in history]

    wins = sum(1 for p in picks if p.outcome == "W")
    losses = sum(1 for p in picks if p.outcome == "L")
    pending = sum(1 for p in picks if p.outcome is None)
    strong_picks = [p for p in picks if p.signal == PickSignal.STRONG]

    print(f"\n{'=' * 40}")
    print("PICK HISTORY")
    print(f"{'=' * 40}")
    print(f"Total picks: {len(picks)}")
    print(f"Record: {wins}W - {losses}L ({pending} pending)")

    if wins + losses > 0:
        win_rate = wins / (wins + losses)
        roi = (wins * 0.91 - losses) / (wins + losses) * 100
        print(f"Win Rate: {win_rate:.1%}")
        print(f"ROI: {roi:+.1f}%")

    if strong_picks:
        strong_wins = sum(1 for p in strong_picks if p.outcome == "W")
        strong_losses = sum(1 for p in strong_picks if p.outcome == "L")
        if strong_wins + strong_losses > 0:
            strong_rate = strong_wins / (strong_wins + strong_losses)
            print(f"\nStrong picks: {strong_wins}W - {strong_losses}L ({strong_rate:.1%})")


def settle_picks() -> None:
    """Interactive settlement of pending picks."""
    if not settings.picks_file.exists():
        print("No picks to settle")
        return

    with open(settings.picks_file) as f:
        history = json.load(f)

    updated = False
    for i, h in enumerate(history):
        if h.get("outcome") is None:
            pick = Pick.from_dict(h)
            print(f"\n{pick.matchup}")
            print(f"Pick: {pick.pick_display} ({pick.confidence}%)")
            result = input("Result (W/L/P/skip): ").strip().upper()

            if result in ("W", "L", "P"):
                history[i]["outcome"] = result
                history[i]["settled_at"] = datetime.now().isoformat()

                if result == "W":
                    history[i]["profit"] = 0.91  # -110 odds
                elif result == "L":
                    history[i]["profit"] = -1.0
                else:
                    history[i]["profit"] = 0.0

                updated = True

    if updated:
        with open(settings.picks_file, "w") as f:
            json.dump(history, f, indent=2)
        print("\nResults saved")
        show_history()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NFL Picks - 65.6% validated accuracy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  picks --week 1 --season 2026    Generate Week 1 picks
  picks --save                    Save picks to history
  picks --history                 View pick history
  picks --settle                  Record outcomes
  picks --serve                   Start web server
        """,
    )
    parser.add_argument("--week", type=int, help="Week number")
    parser.add_argument("--season", type=int, default=2026, help="Season year")
    parser.add_argument("--save", action="store_true", help="Save picks to history")
    parser.add_argument("--history", action="store_true", help="View history")
    parser.add_argument("--settle", action="store_true", help="Record outcomes")
    parser.add_argument("--serve", action="store_true", help="Start web server")
    parser.add_argument("--all", action="store_true", help="Show all picks (not just high-conf)")

    args = parser.parse_args()

    if args.history:
        show_history()
        return

    if args.settle:
        settle_picks()
        return

    if args.serve:
        from .server import run
        print(f"\nStarting NFL Picks server at http://{settings.host}:{settings.port}")
        print("Press Ctrl+C to stop\n")
        run()
        return

    if not args.week:
        print("Usage: picks --week <week_number> [--season <year>]")
        print("       picks --history")
        print("       picks --settle")
        sys.exit(1)

    print(f"\n{'=' * 55}")
    print(f"NFL PICKS - {args.season} WEEK {args.week}")
    print(f"{'=' * 55}")
    print("Model: V4 RB-NGS | Validated: 65.6% accuracy, +25.3% ROI")

    predictor = Predictor()
    picks = predictor.predict_week(args.season, args.week)

    if not picks:
        print(f"\nNo games found for {args.season} Week {args.week}")
        return

    display_picks(picks)

    if args.save:
        # Only save high-confidence picks
        to_save = [p for p in picks if p.signal != PickSignal.SKIP]
        save_picks(to_save)


if __name__ == "__main__":
    main()
