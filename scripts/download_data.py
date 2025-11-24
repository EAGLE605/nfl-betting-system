#!/usr/bin/env python3
"""
NFL Data Download Script
=========================

Command-line script to download NFL data for the betting system.

Usage:
    python scripts/download_data.py --seasons 2016-2024
    python scripts/download_data.py --seasons 2020,2021,2022
    python scripts/download_data.py --all
    python scripts/download_data.py --force  # Force re-download

Examples:
    # Download last 9 seasons (default)
    python scripts/download_data.py

    # Download specific range
    python scripts/download_data.py --seasons 2016-2024

    # Download specific years
    python scripts/download_data.py --seasons 2020,2021,2022,2023

    # Download all available seasons
    python scripts/download_data.py --all

    # Force re-download (ignore cache)
    python scripts/download_data.py --force

Author: NFL Betting System
Date: 2025-11-23
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_pipeline import NFLDataPipeline, get_available_seasons


def parse_seasons(seasons_arg: str) -> list[int]:
    """
    Parse seasons argument.

    Args:
        seasons_arg: String like "2016-2024" or "2020,2021,2022"

    Returns:
        List of season years

    Examples:
        >>> parse_seasons("2016-2024")
        [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
        >>> parse_seasons("2020,2021,2022")
        [2020, 2021, 2022]
    """
    if "-" in seasons_arg:
        # Range format: 2016-2024
        start, end = seasons_arg.split("-")
        return list(range(int(start), int(end) + 1))
    else:
        # Comma-separated: 2020,2021,2022
        return [int(s.strip()) for s in seasons_arg.split(",")]


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 70)
    print("  NFL BETTING SYSTEM - DATA PIPELINE")
    print("  Download NFL data from nflverse (nflreadpy)")
    print("=" * 70 + "\n")


def print_summary(results: dict, elapsed: float):
    """
    Print download summary.

    Args:
        results: Dictionary of downloaded DataFrames
        elapsed: Time elapsed in seconds
    """
    print("\n" + "=" * 70)
    print("  DOWNLOAD SUMMARY")
    print("=" * 70)

    total_rows = 0
    total_size_mb = 0

    for name, df in results.items():
        rows = len(df)
        cols = len(df.columns)
        size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024

        total_rows += rows
        total_size_mb += size_mb

        print(f"  {name:20s}: {rows:8,} rows, {cols:3d} cols, {size_mb:6.1f} MB")

    print("-" * 70)
    print(f"  {'TOTAL':20s}: {total_rows:8,} rows, {total_size_mb:17.1f} MB")
    print(f"  Time elapsed: {elapsed:.1f} seconds")
    print("=" * 70 + "\n")

    print("[OK] Data saved to: data/raw/")
    print("[OK] Metadata saved to: data/raw/metadata.json")
    print("\nNext steps:")
    print("  1. Run tests: pytest tests/")
    print(
        "  2. Explore data: python -c 'import pandas as pd; df = pd.read_parquet(\"data/raw/schedules_2016_2024.parquet\"); print(df.head())'"
    )
    print("  3. Start feature engineering: python src/feature_engineering.py")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download NFL data for betting system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Download 2016-2024 (default)
  %(prog)s --seasons 2016-2024      # Download specific range
  %(prog)s --seasons 2020,2021      # Download specific years
  %(prog)s --all                    # Download all available seasons
  %(prog)s --force                  # Force re-download (ignore cache)
  %(prog)s --no-pbp                 # Skip play-by-play (faster)
        """,
    )

    parser.add_argument(
        "--seasons",
        type=str,
        default="2016-2024",
        help="Seasons to download (range: 2016-2024, or list: 2020,2021,2022)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available seasons (1999-present)",
    )

    parser.add_argument(
        "--force", action="store_true", help="Force re-download (ignore cache)"
    )

    parser.add_argument(
        "--no-pbp",
        action="store_true",
        help="Skip play-by-play data (faster, but less features)",
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root directory for data storage (default: data/)",
    )

    args = parser.parse_args()

    print_banner()

    # Determine seasons to download
    if args.all:
        seasons = get_available_seasons()
        print(f"Downloading ALL available seasons: {min(seasons)}-{max(seasons)}")
    else:
        seasons = parse_seasons(args.seasons)
        print(f"Downloading seasons: {min(seasons)}-{max(seasons)}")

    if args.force:
        print("WARNING: Force mode - Ignoring cache, will re-download all data")

    if args.no_pbp:
        print("WARNING: Skipping play-by-play data (faster but fewer features)")

    print()

    # Initialize pipeline
    pipeline = NFLDataPipeline(data_dir=args.data_dir)

    # Download data
    try:
        import time

        start_time = time.time()

        results = pipeline.download_all(
            seasons=seasons, include_pbp=not args.no_pbp, force_download=args.force
        )

        elapsed = time.time() - start_time

        # Print summary
        print_summary(results, elapsed)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nTroubleshooting:")
        print("  1. Check internet connection")
        print("  2. Verify nflreadpy is installed: pip install nflreadpy")
        print("  3. Try with --no-pbp flag (play-by-play is large)")
        print("  4. Check logs above for specific error")
        sys.exit(1)


if __name__ == "__main__":
    main()
