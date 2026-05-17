import type { PlayerProp } from '../types';

interface PlayerPropCardProps {
  prop: PlayerProp;
}

export function PlayerPropCard({ prop }: PlayerPropCardProps) {
  const {
    player,
    team,
    opponent,
    propType,
    line,
    prediction,
    projectedValue,
    hitRate,
    matchupGrade,
    confidence
  } = prop;

  // Get player initials for avatar
  const initials = player
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2);

  const gradeClass = matchupGrade.toLowerCase();
  const hitRatePercent = Math.round(hitRate * 100);
  const confidenceClass = confidence.toLowerCase();

  return (
    <div className={`prop-card ${confidenceClass}-prop`}>
      <div className="prop-header">
        <div className="prop-player">
          <div className="avatar">{initials}</div>
          <div className="info">
            <div className="name">{player}</div>
            <div className="team">{team} vs {opponent}</div>
          </div>
        </div>
        <span className={`prop-matchup-grade ${gradeClass}`}>
          {matchupGrade}
        </span>
      </div>

      <div className="prop-type-row">
        <span className="prop-type">{propType}</span>
        <span className={`prop-confidence ${confidenceClass}`}>{confidence}</span>
      </div>

      <div className="prop-body">
        <div className="prop-stat">
          <div className="label">Line</div>
          <div className="value">{line}</div>
        </div>

        <div className="prop-stat">
          <div className="label">Pick</div>
          <div className={`value ${prediction.toLowerCase()}`}>
            {prediction}
          </div>
        </div>

        <div className="prop-stat">
          <div className="label">Projected</div>
          <div className={`value ${prediction === 'OVER' ? 'over' : 'under'}`}>
            {projectedValue}
          </div>
        </div>
      </div>

      <div className="prop-hit-rate">
        <div className="hit-rate-label">
          <span>Hit Rate</span>
          <span className="hit-rate-value">{hitRatePercent}%</span>
        </div>
        <div className="hit-rate-bar">
          <div
            className="hit-rate-fill"
            style={{ width: `${hitRatePercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Add additional styles for player props
const style = document.createElement('style');
style.textContent = `
  .prop-type-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-color);
  }

  .prop-type {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .prop-confidence {
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .prop-confidence.high {
    background: var(--accent-green-dim);
    color: var(--accent-green);
  }

  .prop-confidence.medium {
    background: var(--accent-gold-dim);
    color: var(--accent-gold);
  }

  .prop-confidence.low {
    background: rgba(107, 107, 123, 0.2);
    color: var(--text-muted);
  }

  .prop-hit-rate {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
  }

  .hit-rate-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    margin-bottom: 8px;
  }

  .hit-rate-label span:first-child {
    color: var(--text-muted);
  }

  .hit-rate-value {
    font-weight: 600;
    color: var(--accent-green);
  }

  .hit-rate-bar {
    height: 6px;
    background: var(--bg-secondary);
    border-radius: 3px;
    overflow: hidden;
  }

  .hit-rate-fill {
    height: 100%;
    background: var(--gradient-fire);
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .high-prop {
    border-left: 3px solid var(--accent-green);
  }

  .medium-prop {
    border-left: 3px solid var(--accent-gold);
  }

  .low-prop {
    border-left: 3px solid var(--text-muted);
  }
`;
document.head.appendChild(style);
