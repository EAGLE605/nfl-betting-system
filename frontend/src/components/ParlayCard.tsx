import type { Parlay } from '../types';

interface ParlayCardProps {
  parlay: Parlay;
}

export function ParlayCard({ parlay }: ParlayCardProps) {
  const {
    name,
    legs,
    totalOdds,
    modelProbability,
    expectedValue,
    confidence
  } = parlay;

  const formattedOdds = totalOdds >= 0 ? `+${totalOdds}` : totalOdds.toString();
  const evPercent = (expectedValue * 100).toFixed(1);
  const modelProbPercent = (modelProbability * 100).toFixed(0);
  const confidenceClass = confidence.toLowerCase();

  return (
    <div className={`parlay-card ${confidenceClass}-parlay`}>
      <div className="parlay-header">
        <div className="name-section">
          <span className="name">{name}</span>
          <span className={`parlay-confidence-badge ${confidenceClass}`}>
            {confidence}
          </span>
        </div>
        <div className="odds-display">
          <div className="total-odds">{formattedOdds}</div>
          <div className="ev-tag">+{evPercent}% EV</div>
        </div>
      </div>

      <div className="parlay-legs">
        {legs.map((leg, index) => (
          <div key={leg.id} className="parlay-leg">
            <span className="leg-number">{index + 1}</span>
            <div className="leg-details">
              <div className="leg-pick">{leg.prediction}</div>
              <div className="leg-game">{leg.game}</div>
            </div>
            <span className="leg-odds">
              {leg.odds >= 0 ? `+${leg.odds}` : leg.odds}
            </span>
          </div>
        ))}
      </div>

      <div className="parlay-footer">
        <div className="metric">
          <div className="metric-label">Legs</div>
          <div className="metric-value">{legs.length}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Model Prob</div>
          <div className="metric-value">{modelProbPercent}%</div>
        </div>
        <div className="metric">
          <div className="metric-label">Expected Value</div>
          <div className="metric-value positive">+{evPercent}%</div>
        </div>
      </div>
    </div>
  );
}

// Add additional styles for parlay confidence
const style = document.createElement('style');
style.textContent = `
  .name-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .parlay-confidence-badge {
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .parlay-confidence-badge.high {
    background: var(--accent-green-dim);
    color: var(--accent-green);
  }

  .parlay-confidence-badge.medium {
    background: var(--accent-gold-dim);
    color: var(--accent-gold);
  }

  .parlay-confidence-badge.low {
    background: rgba(107, 107, 123, 0.2);
    color: var(--text-muted);
  }

  .metric-value.positive {
    color: var(--accent-green);
  }
`;
document.head.appendChild(style);
