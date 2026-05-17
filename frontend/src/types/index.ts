export interface Pick {
  id: string;
  type: 'spread' | 'total' | 'moneyline' | 'player_prop';
  game: string;
  team?: string;
  player?: string;
  line: number;
  odds: number;
  prediction: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  edge: string;
  winProbability: number;
  reasoning: string;
}

export interface Parlay {
  id: string;
  name: string;
  legs: Pick[];
  totalOdds: number;
  impliedProbability: number;
  modelProbability: number;
  expectedValue: number;
  correlationScore: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface PlayerProp {
  id: string;
  player: string;
  team: string;
  opponent: string;
  propType: string;
  line: number;
  prediction: 'OVER' | 'UNDER';
  projectedValue: number;
  hitRate: number;
  matchupGrade: 'SMASH' | 'PLUS' | 'NEUTRAL' | 'TOUGH' | 'AVOID';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface BettingCard {
  id: string;
  week: number;
  season: number;
  generatedAt: string;
  topPicks: Pick[];
  parlays: Parlay[];
  playerProps: PlayerProp[];
  performance: PerformanceStats;
}

export interface PerformanceStats {
  weeklyRecord: string;
  seasonRecord: string;
  winRate: number;
  roi: number;
  streak: number;
  streakType: 'W' | 'L';
}

export interface Game {
  id: string;
  homeTeam: string;
  awayTeam: string;
  spread: number;
  total: number;
  time: string;
  weather?: string;
}
