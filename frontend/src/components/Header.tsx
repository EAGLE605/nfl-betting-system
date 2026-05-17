
interface HeaderProps {
  week: number;
  season: number;
  weeks?: number[];
  onWeekChange?: (week: number) => void;
}

export function Header({ week, season, weeks = [], onWeekChange }: HeaderProps) {
  return (
    <header className="header">
      <h1>NFL Betting Card</h1>
      <p className="subtitle">AI-Powered Picks, Parlays & Props</p>

      <div className="week-selector-container">
        {weeks.length > 0 && onWeekChange ? (
          <select
            className="week-select"
            value={week}
            onChange={(e) => onWeekChange(Number(e.target.value))}
            aria-label="Select week"
          >
            {weeks.map((w) => (
              <option key={w} value={w}>
                Week {w}
              </option>
            ))}
          </select>
        ) : (
          <span className="week-badge">Week {week}</span>
        )}
        <span className="season-label">{season} Season</span>
      </div>
    </header>
  );
}

// Add styles for the week selector
const style = document.createElement('style');
style.textContent = `
  .week-selector-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 15px;
  }

  .week-select {
    padding: 8px 20px;
    background: var(--accent-gold-dim);
    color: var(--accent-gold);
    border: 1px solid var(--accent-gold);
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffd700' stroke-width='2'%3e%3cpolyline points='6,9 12,15 18,9'/%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 16px;
    padding-right: 36px;
  }

  .week-select:focus {
    outline: none;
    box-shadow: 0 0 0 2px var(--accent-gold-dim);
  }

  .season-label {
    font-size: 0.85rem;
    color: var(--text-muted);
  }
`;
document.head.appendChild(style);
