import type { Pick } from '../types';

interface BettingCardProps {
  pick: Pick;
}

export function BettingCard({ pick }: BettingCardProps) {
  const {
    game,
    prediction,
    odds,
    confidence,
    edge,
    winProbability,
    reasoning
  } = pick;

  const confidenceClass = confidence.toLowerCase();
  const formattedOdds = odds >= 0 ? `+${odds}` : odds.toString();
  const winProbPercent = Math.round(winProbability * 100);

  return (
    <div className={`pick-card ${confidenceClass}-confidence`}>
      <div className="pick-header">
        <div className="game-info">
          <div className="matchup">{game}</div>
          {edge && <span className="edge-tag">{edge}</span>}
        </div>
        <div className="confidence">
          <span className={`confidence-badge ${confidenceClass}`}>
            {confidence}
          </span>
        </div>
      </div>

      <div className="pick-body">
        <div className="pick-details">
          <div className="prediction">{prediction}</div>
          <div className="odds">Odds: {formattedOdds}</div>
          <div className="win-prob">
            <span className="win-prob-label">{winProbPercent}%</span>
            <div className="bar">
              <div
                className="fill"
                style={{ width: `${winProbPercent}%` }}
              />
            </div>
          </div>
        </div>

        {reasoning && (
          <div className="pick-reasoning">
            {reasoning}
          </div>
        )}
      </div>
    </div>
  );
}

// Styles for win probability label
const style = document.createElement('style');
style.textContent = `
  .win-prob-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-secondary);
    min-width: 45px;
  }
`;
document.head.appendChild(style);
