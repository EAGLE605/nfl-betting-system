import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import {
  Header,
  PerformanceBanner,
  BettingCard,
  ParlayCard,
  PlayerPropCard
} from './components';
import { usePicks, usePullToRefresh } from './hooks/usePicks';

function HomePage() {
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const { bettingCard, loading, error, refetch } = usePicks({
    week: selectedWeek,
    useMockData: true // Set to false when API is available
  });

  const { isRefreshing } = usePullToRefresh(refetch);

  const handleWeekChange = useCallback((week: number) => {
    setSelectedWeek(week);
  }, []);

  // Generate available weeks (1-18 for NFL season)
  const availableWeeks = Array.from({ length: 18 }, (_, i) => i + 1);

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner" />
          <div className="text">Loading picks...</div>
        </div>
      </div>
    );
  }

  if (!bettingCard) {
    return (
      <div className="app">
        <div className="empty-state">
          <div className="icon">&#127944;</div>
          <h2>No picks available</h2>
          <p>Check back later for this week's betting card.</p>
        </div>
      </div>
    );
  }

  const { week, season, topPicks, parlays, playerProps, performance } = bettingCard;

  return (
    <div className="app">
      {/* Pull to refresh indicator */}
      {isRefreshing && (
        <div className="refresh-indicator">
          <div className="spinner small" />
          <span>Refreshing...</span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="error-banner">
          <span>{error}</span>
        </div>
      )}

      {/* Header with week selector */}
      <Header
        week={week}
        season={season}
        weeks={availableWeeks}
        onWeekChange={handleWeekChange}
      />

      {/* Performance Stats */}
      <PerformanceBanner stats={performance} />

      {/* Top Picks Section */}
      <section>
        <div className="section-header">
          <h2>Top Picks</h2>
          <span className="badge">{topPicks.length} Picks</span>
        </div>
        <div className="picks-grid">
          {topPicks.map(pick => (
            <BettingCard key={pick.id} pick={pick} />
          ))}
        </div>
      </section>

      {/* Featured Parlays Section */}
      {parlays.length > 0 && (
        <section>
          <div className="section-header">
            <h2>Featured Parlays</h2>
            <span className="badge">{parlays.length} Parlays</span>
          </div>
          {parlays.map(parlay => (
            <ParlayCard key={parlay.id} parlay={parlay} />
          ))}
        </section>
      )}

      {/* Player Props Section */}
      {playerProps.length > 0 && (
        <section>
          <div className="section-header">
            <h2>Player Props</h2>
            <span className="badge">{playerProps.length} Props</span>
          </div>
          <div className="props-grid">
            {playerProps.map(prop => (
              <PlayerPropCard key={prop.id} prop={prop} />
            ))}
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>Generated at {new Date(bettingCard.generatedAt).toLocaleString()}</p>
        <p className="disclaimer">
          For entertainment purposes only. Please gamble responsibly.
        </p>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/week/:weekNum" element={<HomePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

// Add global styles for App-specific elements
const style = document.createElement('style');
style.textContent = `
  .refresh-indicator {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 12px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    z-index: 1000;
    animation: slideDown 0.3s ease;
  }

  @keyframes slideDown {
    from {
      transform: translateY(-100%);
    }
    to {
      transform: translateY(0);
    }
  }

  .spinner.small {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }

  .error-banner {
    background: var(--accent-gold-dim);
    color: var(--accent-gold);
    padding: 12px 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    text-align: center;
    font-size: 0.9rem;
  }

  .picks-grid {
    display: grid;
    gap: 16px;
  }

  .props-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }

  .app-footer {
    margin-top: 60px;
    padding: 30px 20px;
    text-align: center;
    border-top: 1px solid var(--border-color);
  }

  .app-footer p {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 8px;
  }

  .app-footer .disclaimer {
    font-size: 0.75rem;
    color: var(--text-muted);
    opacity: 0.7;
  }

  /* PWA safe area for iOS notch */
  @supports (padding-top: env(safe-area-inset-top)) {
    .app {
      padding-top: calc(20px + env(safe-area-inset-top));
      padding-bottom: calc(20px + env(safe-area-inset-bottom));
      padding-left: calc(20px + env(safe-area-inset-left));
      padding-right: calc(20px + env(safe-area-inset-right));
    }
  }

  /* Mobile optimizations */
  @media (max-width: 768px) {
    .props-grid {
      grid-template-columns: 1fr;
    }

    .app {
      padding: 16px;
    }

    .section-header {
      margin: 30px 0 16px;
    }

    .section-header h2 {
      font-size: 1.3rem;
    }
  }

  /* Prevent text selection on touch devices for better feel */
  @media (pointer: coarse) {
    .pick-card,
    .parlay-card,
    .prop-card,
    .stat-card {
      -webkit-user-select: none;
      user-select: none;
    }
  }

  /* Smooth scrolling */
  html {
    scroll-behavior: smooth;
  }

  /* Active states for touch */
  .pick-card:active,
  .parlay-card:active,
  .prop-card:active {
    transform: scale(0.98);
    transition: transform 0.1s ease;
  }
`;
document.head.appendChild(style);
