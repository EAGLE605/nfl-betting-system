import type { PerformanceStats } from '../types';

interface PerformanceBannerProps {
  stats: PerformanceStats;
}

export function PerformanceBanner({ stats }: PerformanceBannerProps) {
  const { weeklyRecord, seasonRecord, winRate, roi, streak, streakType } = stats;

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatROI = (value: number) => {
    const percent = (value * 100).toFixed(1);
    return value >= 0 ? `+${percent}%` : `${percent}%`;
  };

  return (
    <div className="performance-banner">
      <div className="stat-card">
        <div className="label">This Week</div>
        <div className="value">{weeklyRecord}</div>
      </div>

      <div className="stat-card">
        <div className="label">Season Record</div>
        <div className="value">{seasonRecord}</div>
      </div>

      <div className="stat-card">
        <div className="label">Win Rate</div>
        <div className={`value ${winRate >= 0.55 ? 'positive' : winRate < 0.5 ? 'negative' : ''}`}>
          {formatPercent(winRate)}
        </div>
      </div>

      <div className="stat-card">
        <div className="label">ROI</div>
        <div className={`value ${roi >= 0 ? 'positive' : 'negative'}`}>
          {formatROI(roi)}
        </div>
      </div>

      <div className="stat-card">
        <div className="label">Streak</div>
        <div className={`value ${streakType === 'W' ? 'positive' : 'negative'}`}>
          {streak}{streakType}
        </div>
      </div>
    </div>
  );
}
