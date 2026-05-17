import type { BettingCard, Pick, Parlay, PlayerProp, PerformanceStats } from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBettingCard(week?: number): Promise<BettingCard> {
  const params = week ? `?week=${week}` : '';
  return fetchJson<BettingCard>(`${API_BASE}/betting-card${params}`);
}

export async function fetchTopPicks(week?: number): Promise<Pick[]> {
  const params = week ? `?week=${week}` : '';
  return fetchJson<Pick[]>(`${API_BASE}/picks${params}`);
}

export async function fetchParlays(week?: number): Promise<Parlay[]> {
  const params = week ? `?week=${week}` : '';
  return fetchJson<Parlay[]>(`${API_BASE}/parlays${params}`);
}

export async function fetchPlayerProps(week?: number): Promise<PlayerProp[]> {
  const params = week ? `?week=${week}` : '';
  return fetchJson<PlayerProp[]>(`${API_BASE}/player-props${params}`);
}

export async function fetchPerformance(): Promise<PerformanceStats> {
  return fetchJson<PerformanceStats>(`${API_BASE}/performance`);
}

export async function fetchCurrentWeek(): Promise<{ week: number; season: number }> {
  return fetchJson<{ week: number; season: number }>(`${API_BASE}/current-week`);
}

export async function fetchWeeks(): Promise<number[]> {
  return fetchJson<number[]>(`${API_BASE}/weeks`);
}

// Mock data for development/demo when API is unavailable
export function getMockBettingCard(): BettingCard {
  return {
    id: 'mock-card-1',
    week: 12,
    season: 2025,
    generatedAt: new Date().toISOString(),
    topPicks: [
      {
        id: 'pick-1',
        type: 'spread',
        game: 'Chiefs @ Raiders',
        team: 'Kansas City Chiefs',
        line: -7.5,
        odds: -110,
        prediction: 'Chiefs -7.5',
        confidence: 'HIGH',
        edge: 'Sharp Money',
        winProbability: 0.72,
        reasoning: 'Chiefs defense has been dominant against divisional opponents. Raiders struggling with injuries on O-line.'
      },
      {
        id: 'pick-2',
        type: 'total',
        game: 'Bills @ Dolphins',
        line: 51.5,
        odds: -105,
        prediction: 'Over 51.5',
        confidence: 'HIGH',
        edge: 'Weather Model',
        winProbability: 0.68,
        reasoning: 'Perfect weather conditions in Miami. Both offenses averaging 30+ points in dome/warm weather games.'
      },
      {
        id: 'pick-3',
        type: 'spread',
        game: '49ers @ Seahawks',
        team: 'San Francisco 49ers',
        line: -3.5,
        odds: -115,
        prediction: '49ers -3.5',
        confidence: 'MEDIUM',
        edge: 'Injury Report',
        winProbability: 0.61,
        reasoning: 'Seattle missing two starting CBs. 49ers WR corps healthy and ready for a big game.'
      },
      {
        id: 'pick-4',
        type: 'moneyline',
        game: 'Ravens @ Bengals',
        team: 'Baltimore Ravens',
        line: 0,
        odds: -145,
        prediction: 'Ravens ML',
        confidence: 'MEDIUM',
        edge: 'Public Fade',
        winProbability: 0.59,
        reasoning: 'Ravens 8-2 ATS as road favorites this season. Lamar Jackson perfect record vs Bengals when healthy.'
      }
    ],
    parlays: [
      {
        id: 'parlay-1',
        name: 'Premium Lock Parlay',
        legs: [
          {
            id: 'leg-1',
            type: 'spread',
            game: 'Chiefs @ Raiders',
            team: 'Chiefs',
            line: -7.5,
            odds: -110,
            prediction: 'Chiefs -7.5',
            confidence: 'HIGH',
            edge: 'Sharp Money',
            winProbability: 0.72,
            reasoning: ''
          },
          {
            id: 'leg-2',
            type: 'total',
            game: 'Bills @ Dolphins',
            line: 51.5,
            odds: -105,
            prediction: 'Over 51.5',
            confidence: 'HIGH',
            edge: 'Weather',
            winProbability: 0.68,
            reasoning: ''
          },
          {
            id: 'leg-3',
            type: 'spread',
            game: 'Lions @ Bears',
            team: 'Lions',
            line: -6.5,
            odds: -110,
            prediction: 'Lions -6.5',
            confidence: 'HIGH',
            edge: 'Power Rating',
            winProbability: 0.70,
            reasoning: ''
          }
        ],
        totalOdds: 595,
        impliedProbability: 0.144,
        modelProbability: 0.343,
        expectedValue: 0.138,
        correlationScore: 0.12,
        confidence: 'HIGH'
      },
      {
        id: 'parlay-2',
        name: 'Underdog Special',
        legs: [
          {
            id: 'leg-4',
            type: 'moneyline',
            game: 'Jets @ Patriots',
            team: 'Jets',
            line: 0,
            odds: 135,
            prediction: 'Jets ML',
            confidence: 'MEDIUM',
            edge: 'Value',
            winProbability: 0.52,
            reasoning: ''
          },
          {
            id: 'leg-5',
            type: 'spread',
            game: 'Cowboys @ Commanders',
            team: 'Commanders',
            line: 2.5,
            odds: -105,
            prediction: 'Commanders +2.5',
            confidence: 'MEDIUM',
            edge: 'Home Dog',
            winProbability: 0.55,
            reasoning: ''
          }
        ],
        totalOdds: 325,
        impliedProbability: 0.235,
        modelProbability: 0.286,
        expectedValue: 0.082,
        correlationScore: 0.05,
        confidence: 'MEDIUM'
      }
    ],
    playerProps: [
      {
        id: 'prop-1',
        player: 'Patrick Mahomes',
        team: 'KC',
        opponent: 'LV',
        propType: 'Passing Yards',
        line: 275.5,
        prediction: 'OVER',
        projectedValue: 302,
        hitRate: 0.75,
        matchupGrade: 'SMASH',
        confidence: 'HIGH'
      },
      {
        id: 'prop-2',
        player: 'Tyreek Hill',
        team: 'MIA',
        opponent: 'BUF',
        propType: 'Receiving Yards',
        line: 84.5,
        prediction: 'OVER',
        projectedValue: 98,
        hitRate: 0.68,
        matchupGrade: 'PLUS',
        confidence: 'HIGH'
      },
      {
        id: 'prop-3',
        player: 'Derrick Henry',
        team: 'BAL',
        opponent: 'CIN',
        propType: 'Rushing Yards',
        line: 89.5,
        prediction: 'OVER',
        projectedValue: 105,
        hitRate: 0.71,
        matchupGrade: 'SMASH',
        confidence: 'HIGH'
      },
      {
        id: 'prop-4',
        player: 'CeeDee Lamb',
        team: 'DAL',
        opponent: 'WSH',
        propType: 'Receptions',
        line: 6.5,
        prediction: 'OVER',
        projectedValue: 8,
        hitRate: 0.64,
        matchupGrade: 'NEUTRAL',
        confidence: 'MEDIUM'
      }
    ],
    performance: {
      weeklyRecord: '8-4',
      seasonRecord: '89-52',
      winRate: 0.631,
      roi: 0.142,
      streak: 5,
      streakType: 'W'
    }
  };
}
