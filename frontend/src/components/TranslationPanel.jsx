import React from 'react';
import { Globe2, Volume2, AlertCircle } from 'lucide-react';

export function TranslationPanel({ translation, targetLang, warning, isOffline }) {
  const langLabels = {
    en: 'English',
    ta: 'Tamil — தமிழ்',
    te: 'Telugu — తెలుగు',
    kn: 'Kannada — ಕನ್ನಡ',
    ml: 'Malayalam — മലയാളം',
    hi: 'Hindi — हिन्दी',
    sat: 'Santhali — ᱥᱟᱱᱛᱟᱲᱤ',
    hoc: 'Ho — Ho (हो)',
    unr: 'Mundari — Mundari (मुंडारी)',
  };

  return (
    <div className="hud-panel" style={{ backgroundColor: 'var(--bg-surface-secondary)' }}>
      <div className="hud-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe2 size={15} color="var(--primary)" />
          <span className="hud-title">
            Live Translation ({langLabels[targetLang] || targetLang.toUpperCase()})
          </span>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {isOffline && (
            <span className="model-badge" style={{ backgroundColor: 'var(--warning-light)', color: 'var(--warning-text)' }}>
              Offline Cache
            </span>
          )}
          <span className="model-badge indic">IndicTrans2</span>
        </div>
      </div>

      <div className="hud-content" style={{ color: translation ? 'var(--text-primary)' : 'var(--text-dim)', fontWeight: 500 }}>
        {translation || 'Translation will appear here in real-time...'}
      </div>

      {warning && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--warning-text)', marginTop: '10px', padding: '6px 10px', backgroundColor: 'var(--warning-light)', borderRadius: 'var(--radius-sm)' }}>
          <AlertCircle size={14} />
          <span>{warning}</span>
        </div>
      )}
    </div>
  );
}
