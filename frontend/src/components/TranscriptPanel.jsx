import React from 'react';
import { Mic, User } from 'lucide-react';

export function TranscriptPanel({ transcript, sourceLang, detectedLang }) {
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
    <div className="hud-panel">
      <div className="hud-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <User size={15} color="var(--primary)" />
          <span className="hud-title">
            Source Transcript ({langLabels[sourceLang] || sourceLang.toUpperCase()})
          </span>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {detectedLang && detectedLang !== sourceLang && (
            <span className="model-badge" style={{ backgroundColor: 'var(--primary-light)', color: 'var(--primary)' }}>
              Detected: {detectedLang.toUpperCase()}
            </span>
          )}
          <span className="model-badge">Speaker Audio</span>
        </div>
      </div>

      <div className="hud-content" style={{ color: transcript ? 'var(--text-primary)' : 'var(--text-dim)' }}>
        {transcript || 'Speak into the microphone to see real-time transcription...'}
      </div>
    </div>
  );
}
