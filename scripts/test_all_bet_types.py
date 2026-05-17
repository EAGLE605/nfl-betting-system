"""Test ALL Bet Types for Frontend Cards

Tests every prop and SGP type from popular_bets.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")


def load_pbp():
    """Load play-by-play data."""
    return pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")


def test_receiving_yards(pbp):
    """Test receiving yards props."""
    print("\n" + "=" * 60)
    print("1. RECEIVING YARDS PROPS")
    print("=" * 60)
    
    # Aggregate receiving yards by player per game
    rec = pbp[pbp['play_type'] == 'pass'].groupby(
        ['game_id', 'season', 'week', 'receiver_player_name', 'posteam']
    )['receiving_yards'].sum().reset_index()
    rec = rec[rec['receiver_player_name'].notna()]
    rec = rec[rec['receiving_yards'] > 0]
    
    print(f"Total player-games: {len(rec):,}")
    
    # Test common lines
    lines = [39.5, 49.5, 59.5, 69.5, 79.5]
    
    print(f"\n{'Line':<10} {'Over %':<12} {'Under %':<12} {'N':<10}")
    print("-" * 50)
    
    results = []
    for line in lines:
        over_pct = (rec['receiving_yards'] > line).mean()
        under_pct = 1 - over_pct
        n = len(rec)
        
        # Breakeven at -110 is 52.4%
        over_edge = (over_pct - 0.524) * 100
        under_edge = (under_pct - 0.524) * 100
        
        print(f"{line:<10} {over_pct:.1%}        {under_pct:.1%}        {n:,}")
        results.append({'prop': 'receiving_yards', 'line': line, 'over_pct': over_pct, 'under_pct': under_pct})
    
    return results


def test_rushing_yards(pbp):
    """Test rushing yards props."""
    print("\n" + "=" * 60)
    print("2. RUSHING YARDS PROPS")
    print("=" * 60)
    
    rush = pbp[pbp['play_type'] == 'run'].groupby(
        ['game_id', 'season', 'week', 'rusher_player_name', 'posteam']
    )['rushing_yards'].sum().reset_index()
    rush = rush[rush['rusher_player_name'].notna()]
    rush = rush[rush['rushing_yards'] > 0]
    
    print(f"Total player-games: {len(rush):,}")
    
    lines = [44.5, 54.5, 64.5, 74.5, 84.5]
    
    print(f"\n{'Line':<10} {'Over %':<12} {'Under %':<12} {'N':<10}")
    print("-" * 50)
    
    results = []
    for line in lines:
        over_pct = (rush['rushing_yards'] > line).mean()
        under_pct = 1 - over_pct
        n = len(rush)
        print(f"{line:<10} {over_pct:.1%}        {under_pct:.1%}        {n:,}")
        results.append({'prop': 'rushing_yards', 'line': line, 'over_pct': over_pct, 'under_pct': under_pct})
    
    return results


def test_receptions(pbp):
    """Test receptions props."""
    print("\n" + "=" * 60)
    print("3. RECEPTIONS PROPS")
    print("=" * 60)
    
    rec = pbp[(pbp['play_type'] == 'pass') & (pbp['complete_pass'] == 1)].groupby(
        ['game_id', 'season', 'week', 'receiver_player_name', 'posteam']
    ).size().reset_index(name='receptions')
    rec = rec[rec['receiver_player_name'].notna()]
    
    print(f"Total player-games: {len(rec):,}")
    
    lines = [3.5, 4.5, 5.5, 6.5, 7.5]
    
    print(f"\n{'Line':<10} {'Over %':<12} {'Under %':<12} {'N':<10}")
    print("-" * 50)
    
    results = []
    for line in lines:
        over_pct = (rec['receptions'] > line).mean()
        under_pct = 1 - over_pct
        n = len(rec)
        print(f"{line:<10} {over_pct:.1%}        {under_pct:.1%}        {n:,}")
        results.append({'prop': 'receptions', 'line': line, 'over_pct': over_pct, 'under_pct': under_pct})
    
    return results


def test_passing_yards(pbp):
    """Test passing yards props."""
    print("\n" + "=" * 60)
    print("4. PASSING YARDS PROPS")
    print("=" * 60)
    
    passing = pbp[pbp['play_type'] == 'pass'].groupby(
        ['game_id', 'season', 'week', 'passer_player_name', 'posteam']
    )['passing_yards'].sum().reset_index()
    passing = passing[passing['passer_player_name'].notna()]
    passing = passing[passing['passing_yards'] > 50]  # Filter to starters
    
    print(f"Total QB-games: {len(passing):,}")
    
    lines = [199.5, 224.5, 249.5, 274.5, 299.5]
    
    print(f"\n{'Line':<10} {'Over %':<12} {'Under %':<12} {'N':<10}")
    print("-" * 50)
    
    results = []
    for line in lines:
        over_pct = (passing['passing_yards'] > line).mean()
        under_pct = 1 - over_pct
        n = len(passing)
        print(f"{line:<10} {over_pct:.1%}        {under_pct:.1%}        {n:,}")
        results.append({'prop': 'passing_yards', 'line': line, 'over_pct': over_pct, 'under_pct': under_pct})
    
    return results


def test_passing_tds(pbp):
    """Test passing TDs props."""
    print("\n" + "=" * 60)
    print("5. PASSING TDS PROPS")
    print("=" * 60)
    
    passing = pbp[pbp['pass_touchdown'] == 1].groupby(
        ['game_id', 'season', 'week', 'passer_player_name', 'posteam']
    ).size().reset_index(name='pass_tds')
    
    # Get all QB games (including 0 TD games)
    all_qb = pbp[pbp['play_type'] == 'pass'].groupby(
        ['game_id', 'season', 'week', 'passer_player_name', 'posteam']
    )['passing_yards'].sum().reset_index()
    all_qb = all_qb[all_qb['passer_player_name'].notna()]
    all_qb = all_qb[all_qb['passing_yards'] > 50]
    
    all_qb = all_qb.merge(passing, on=['game_id', 'season', 'week', 'passer_player_name', 'posteam'], how='left')
    all_qb['pass_tds'] = all_qb['pass_tds'].fillna(0)
    
    print(f"Total QB-games: {len(all_qb):,}")
    
    lines = [0.5, 1.5, 2.5]
    
    print(f"\n{'Line':<10} {'Over %':<12} {'Under %':<12} {'N':<10}")
    print("-" * 50)
    
    results = []
    for line in lines:
        over_pct = (all_qb['pass_tds'] > line).mean()
        under_pct = 1 - over_pct
        n = len(all_qb)
        print(f"{line:<10} {over_pct:.1%}        {under_pct:.1%}        {n:,}")
        results.append({'prop': 'passing_tds', 'line': line, 'over_pct': over_pct, 'under_pct': under_pct})
    
    return results


def test_anytime_td(pbp):
    """Test anytime TD scorer props."""
    print("\n" + "=" * 60)
    print("6. ANYTIME TD SCORER PROPS")
    print("=" * 60)
    
    # Receiving TDs
    rec_td = pbp[pbp['pass_touchdown'] == 1].groupby(
        ['game_id', 'season', 'week', 'receiver_player_name', 'posteam']
    ).size().reset_index(name='rec_tds')
    rec_td = rec_td.rename(columns={'receiver_player_name': 'player'})
    
    # Rushing TDs
    rush_td = pbp[pbp['rush_touchdown'] == 1].groupby(
        ['game_id', 'season', 'week', 'rusher_player_name', 'posteam']
    ).size().reset_index(name='rush_tds')
    rush_td = rush_td.rename(columns={'rusher_player_name': 'player'})
    
    # Combine
    tds = rec_td.merge(rush_td, on=['game_id', 'season', 'week', 'player', 'posteam'], how='outer')
    tds['rec_tds'] = tds['rec_tds'].fillna(0)
    tds['rush_tds'] = tds['rush_tds'].fillna(0)
    tds['total_tds'] = tds['rec_tds'] + tds['rush_tds']
    tds = tds[tds['player'].notna()]
    
    # Get all skill players (appeared in a play)
    skill_players = set()
    for col in ['receiver_player_name', 'rusher_player_name']:
        skill_players.update(pbp[pbp[col].notna()][col].unique())
    
    # Count games per player
    rec_games = pbp[pbp['receiver_player_name'].notna()].groupby(
        ['game_id', 'receiver_player_name']
    ).size().reset_index().rename(columns={'receiver_player_name': 'player'})
    
    rush_games = pbp[pbp['rusher_player_name'].notna()].groupby(
        ['game_id', 'rusher_player_name']
    ).size().reset_index().rename(columns={'rusher_player_name': 'player'})
    
    all_games = pd.concat([rec_games[['game_id', 'player']], rush_games[['game_id', 'player']]]).drop_duplicates()
    all_games = all_games.merge(tds[['game_id', 'player', 'total_tds']], on=['game_id', 'player'], how='left')
    all_games['total_tds'] = all_games['total_tds'].fillna(0)
    all_games['scored_td'] = (all_games['total_tds'] > 0).astype(int)
    
    print(f"Total player-games: {len(all_games):,}")
    
    # Overall anytime TD rate
    td_rate = all_games['scored_td'].mean()
    print(f"\nOverall Anytime TD rate: {td_rate:.1%}")
    
    # By position (approximated by activity)
    # Players with more rush attempts are likely RBs
    rush_heavy = pbp[pbp['rusher_player_name'].notna()].groupby('rusher_player_name').size()
    rush_heavy = rush_heavy[rush_heavy > 50].index.tolist()
    
    rb_games = all_games[all_games['player'].isin(rush_heavy)]
    wr_games = all_games[~all_games['player'].isin(rush_heavy)]
    
    print(f"\nRB Anytime TD rate: {rb_games['scored_td'].mean():.1%} (n={len(rb_games):,})")
    print(f"WR/TE Anytime TD rate: {wr_games['scored_td'].mean():.1%} (n={len(wr_games):,})")
    
    return [{'prop': 'anytime_td', 'line': 0.5, 'over_pct': td_rate}]


def test_first_td(pbp):
    """Test first TD scorer props."""
    print("\n" + "=" * 60)
    print("7. FIRST TD SCORER PROPS")
    print("=" * 60)
    
    # Get first TD of each game
    tds = pbp[(pbp['pass_touchdown'] == 1) | (pbp['rush_touchdown'] == 1)].copy()
    tds = tds.sort_values(['game_id', 'game_seconds_remaining'], ascending=[True, False])
    
    first_tds = tds.groupby('game_id').first().reset_index()
    
    # Identify scorer
    first_tds['scorer'] = first_tds['receiver_player_name'].fillna(first_tds['rusher_player_name'])
    first_tds = first_tds[first_tds['scorer'].notna()]
    
    print(f"Total games with TDs: {len(first_tds):,}")
    
    # Count how often each player is first TD scorer
    scorer_counts = first_tds['scorer'].value_counts()
    total_games = first_tds['game_id'].nunique()
    
    print(f"\nTop First TD Scorers:")
    for player, count in scorer_counts.head(10).items():
        pct = count / total_games
        print(f"  {player}: {count} times ({pct:.1%})")
    
    # Average first TD rate per player
    avg_first_td_rate = 1 / len(scorer_counts)  # Rough estimate
    print(f"\nAverage player First TD rate: ~{avg_first_td_rate:.1%}")
    
    return [{'prop': 'first_td', 'line': 0, 'over_pct': avg_first_td_rate}]


def test_sgp_correlations(pbp):
    """Test SGP correlation templates."""
    print("\n" + "=" * 60)
    print("SGP CORRELATION TESTS")
    print("=" * 60)
    
    # Build player stats per game
    games = pbp.groupby('game_id').first()[['season', 'week', 'home_team', 'away_team']].reset_index()
    
    # QB stats
    qb_stats = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'passer_player_name', 'posteam']).agg({
        'passing_yards': 'sum',
        'pass_touchdown': 'sum',
    }).reset_index()
    qb_stats = qb_stats[qb_stats['passing_yards'] > 50]
    qb_stats.columns = ['game_id', 'qb', 'team', 'qb_pass_yards', 'qb_pass_tds']
    
    # WR stats
    wr_stats = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'receiver_player_name', 'posteam']).agg({
        'receiving_yards': 'sum',
        'complete_pass': 'sum',
        'pass_touchdown': 'sum',
    }).reset_index()
    wr_stats = wr_stats[wr_stats['receiver_player_name'].notna()]
    wr_stats.columns = ['game_id', 'wr', 'team', 'wr_rec_yards', 'wr_receptions', 'wr_rec_tds']
    
    # RB stats
    rb_rush = pbp[pbp['play_type'] == 'run'].groupby(['game_id', 'rusher_player_name', 'posteam']).agg({
        'rushing_yards': 'sum',
    }).reset_index()
    rb_rush.columns = ['game_id', 'rb', 'team', 'rb_rush_yards']
    
    rb_rec = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'receiver_player_name', 'posteam']).agg({
        'receiving_yards': 'sum',
    }).reset_index()
    rb_rec.columns = ['game_id', 'rb', 'team', 'rb_rec_yards']
    
    # Test correlations
    print("\n1. QB + WR Stack (same team)")
    # Merge QB and WR on same team
    qb_wr = qb_stats.merge(wr_stats, on=['game_id', 'team'])
    if len(qb_wr) > 100:
        corr = qb_wr['qb_pass_yards'].corr(qb_wr['wr_rec_yards'])
        print(f"   QB Pass Yards vs WR Rec Yards: r={corr:.3f} (n={len(qb_wr):,})")
    
    print("\n2. RB Dual Threat (same player)")
    rb_dual = rb_rush.merge(rb_rec, on=['game_id', 'rb', 'team'], how='inner')
    rb_dual = rb_dual[(rb_dual['rb_rush_yards'] > 0) & (rb_dual['rb_rec_yards'] > 0)]
    if len(rb_dual) > 100:
        corr = rb_dual['rb_rush_yards'].corr(rb_dual['rb_rec_yards'])
        print(f"   RB Rush Yards vs RB Rec Yards: r={corr:.3f} (n={len(rb_dual):,})")
    
    print("\n3. Volume Receiver (same player)")
    if len(wr_stats) > 100:
        corr = wr_stats['wr_receptions'].corr(wr_stats['wr_rec_yards'])
        print(f"   WR Receptions vs WR Rec Yards: r={corr:.3f} (n={len(wr_stats):,})")
    
    print("\n4. QB Pass Yards vs QB Pass TDs")
    if len(qb_stats) > 100:
        corr = qb_stats['qb_pass_yards'].corr(qb_stats['qb_pass_tds'])
        print(f"   QB Pass Yards vs QB Pass TDs: r={corr:.3f} (n={len(qb_stats):,})")
    
    # WR1 vs WR2 same team
    print("\n5. WR1 vs WR2 (same team)")
    wr_ranked = wr_stats.sort_values(['game_id', 'team', 'wr_rec_yards'], ascending=[True, True, False])
    wr_ranked['rank'] = wr_ranked.groupby(['game_id', 'team']).cumcount() + 1
    wr1 = wr_ranked[wr_ranked['rank'] == 1][['game_id', 'team', 'wr_rec_yards']].rename(columns={'wr_rec_yards': 'wr1_yards'})
    wr2 = wr_ranked[wr_ranked['rank'] == 2][['game_id', 'team', 'wr_rec_yards']].rename(columns={'wr_rec_yards': 'wr2_yards'})
    wr_compare = wr1.merge(wr2, on=['game_id', 'team'])
    if len(wr_compare) > 100:
        corr = wr_compare['wr1_yards'].corr(wr_compare['wr2_yards'])
        print(f"   WR1 Yards vs WR2 Yards: r={corr:.3f} (n={len(wr_compare):,})")


def test_sgp_hit_rates(pbp):
    """Test SGP template hit rates."""
    print("\n" + "=" * 60)
    print("SGP TEMPLATE HIT RATE TESTS")
    print("=" * 60)
    
    # Build combined stats
    qb_stats = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'passer_player_name', 'posteam']).agg({
        'passing_yards': 'sum',
    }).reset_index()
    qb_stats = qb_stats[qb_stats['passing_yards'] > 50]
    qb_stats.columns = ['game_id', 'qb', 'team', 'qb_pass_yards']
    
    wr_stats = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'receiver_player_name', 'posteam']).agg({
        'receiving_yards': 'sum',
    }).reset_index()
    wr_stats = wr_stats[wr_stats['receiver_player_name'].notna()]
    wr_stats.columns = ['game_id', 'wr', 'team', 'wr_rec_yards']
    
    # Get top WR per team per game
    wr_stats = wr_stats.sort_values(['game_id', 'team', 'wr_rec_yards'], ascending=[True, True, False])
    wr1 = wr_stats.groupby(['game_id', 'team']).first().reset_index()
    
    # QB + WR1 Stack
    qb_wr = qb_stats.merge(wr1, on=['game_id', 'team'])
    
    print("\n1. QB + WR1 Stack (QB 225+ pass yards AND WR1 60+ rec yards)")
    if len(qb_wr) > 0:
        both_hit = ((qb_wr['qb_pass_yards'] >= 225) & (qb_wr['wr_rec_yards'] >= 60)).mean()
        qb_hit = (qb_wr['qb_pass_yards'] >= 225).mean()
        wr_hit = (qb_wr['wr_rec_yards'] >= 60).mean()
        independent = qb_hit * wr_hit
        
        print(f"   QB 225+ alone: {qb_hit:.1%}")
        print(f"   WR1 60+ alone: {wr_hit:.1%}")
        print(f"   Independent probability: {independent:.1%}")
        print(f"   Actual joint hit rate: {both_hit:.1%}")
        print(f"   Correlation boost: {(both_hit/independent - 1)*100:+.1f}%")
        print(f"   N = {len(qb_wr):,}")
    
    # RB Dual Threat
    rb_rush = pbp[pbp['play_type'] == 'run'].groupby(['game_id', 'rusher_player_name', 'posteam']).agg({
        'rushing_yards': 'sum',
    }).reset_index()
    rb_rush.columns = ['game_id', 'rb', 'team', 'rb_rush_yards']
    
    rb_rec = pbp[pbp['play_type'] == 'pass'].groupby(['game_id', 'receiver_player_name', 'posteam']).agg({
        'receiving_yards': 'sum',
    }).reset_index()
    rb_rec.columns = ['game_id', 'rb', 'team', 'rb_rec_yards']
    
    rb_dual = rb_rush.merge(rb_rec, on=['game_id', 'rb', 'team'])
    
    print("\n2. RB Dual Threat (RB 50+ rush AND 25+ rec)")
    if len(rb_dual) > 0:
        both_hit = ((rb_dual['rb_rush_yards'] >= 50) & (rb_dual['rb_rec_yards'] >= 25)).mean()
        rush_hit = (rb_dual['rb_rush_yards'] >= 50).mean()
        rec_hit = (rb_dual['rb_rec_yards'] >= 25).mean()
        independent = rush_hit * rec_hit
        
        print(f"   RB 50+ rush alone: {rush_hit:.1%}")
        print(f"   RB 25+ rec alone: {rec_hit:.1%}")
        print(f"   Independent probability: {independent:.1%}")
        print(f"   Actual joint hit rate: {both_hit:.1%}")
        if independent > 0:
            print(f"   Correlation effect: {(both_hit/independent - 1)*100:+.1f}%")
        print(f"   N = {len(rb_dual):,}")


def main():
    print("=" * 60)
    print("COMPREHENSIVE BET TYPE TESTING")
    print("=" * 60)
    print("Testing all prop types and SGP templates from popular_bets.py")
    
    pbp = load_pbp()
    print(f"\nLoaded {len(pbp):,} plays from 4 seasons")
    
    all_results = []
    
    # Test all props
    all_results.extend(test_receiving_yards(pbp))
    all_results.extend(test_rushing_yards(pbp))
    all_results.extend(test_receptions(pbp))
    all_results.extend(test_passing_yards(pbp))
    all_results.extend(test_passing_tds(pbp))
    all_results.extend(test_anytime_td(pbp))
    all_results.extend(test_first_td(pbp))
    
    # Test SGP correlations
    test_sgp_correlations(pbp)
    
    # Test SGP hit rates
    test_sgp_hit_rates(pbp)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: PROFITABLE PROPS (Over > 52.4% breakeven)")
    print("=" * 60)
    
    for r in all_results:
        if r.get('over_pct', 0) > 0.524:
            print(f"  {r['prop']} over {r.get('line', 'N/A')}: {r['over_pct']:.1%} (+EV)")
        if r.get('under_pct', 0) > 0.524:
            print(f"  {r['prop']} under {r.get('line', 'N/A')}: {r['under_pct']:.1%} (+EV)")
    
    return all_results


if __name__ == "__main__":
    results = main()
