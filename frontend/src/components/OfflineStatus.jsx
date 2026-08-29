import React from 'react';

export function OfflineStatus({ isSimulatedOffline, onToggleOffline, cacheCount = 50 }) {
  return (
    <div className="glass-panel" style={{ padding: '16px' }}>
      <div className="offline-switch-box">
        <div>
          <h4 style={{ fontSize: '13px', color: '#fff', marginBottom: '2px' }}>
            {isSimulatedOffline ? '📶 Offline Simulation Active' : '🌐 Online Live Mode'}
          </h4>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            {isSimulatedOffline
              ? 'Serving directly from verified SQLite phrase cache'
              : `${cacheCount}+ verified classroom phrases pre-cached`}
          </p>
        </div>
        <label className="switch-toggle">
          <input
            type="checkbox"
            checked={isSimulatedOffline}
            onChange={(e) => onToggleOffline(e.target.checked)}
          />
          <span className="slider"></span>
        </label>
      </div>
    </div>
  );
}
