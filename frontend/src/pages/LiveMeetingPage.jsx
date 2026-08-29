import React, { useState } from 'react';
import { Radio, Monitor, Sliders, ExternalLink, Play, Check, Shield } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';

export function LiveMeetingPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();
  const [hudOpacity, setHudOpacity] = useState(90);
  const [hudFontSize, setHudFontSize] = useState(16);
  const [isSimulating, setIsSimulating] = useState(true);

  return (
    <div className="page-container">
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Live Classroom & Meeting Translation
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Capture tab audio or microphone stream in real-time and render floating subtitles on Google Meet, Zoom, or web lectures
        </p>
      </div>

      {/* Language Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px' }}>
        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Left Side: Floating HUD Preview */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Floating Subtitle HUD Preview
            </span>
            <button
              className="icon-action-btn"
              onClick={() => setIsSimulating(!isSimulating)}
              style={{ fontSize: '12px', padding: '4px 10px' }}
            >
              {isSimulating ? 'Pause Stream' : 'Resume Stream'}
            </button>
          </div>

          {/* Simulated Floating HUD Overlay */}
          <div
            style={{
              borderRadius: 'var(--radius-lg)',
              backgroundColor: `rgba(23, 32, 51, ${hudOpacity / 100})`,
              color: '#ffffff',
              padding: '20px',
              boxShadow: 'var(--shadow-lg)',
              minHeight: '220px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, padding: '2px 6px', backgroundColor: 'var(--primary)', borderRadius: '4px' }}>
                  TRANSLARA HUD
                </span>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>
                  {sourceLang.toUpperCase()} ⇄ {targetLang.toUpperCase()}
                </span>
              </div>
              <span style={{ fontSize: '11px', color: '#34D399', fontWeight: 700 }}>
                ● LIVE
              </span>
            </div>

            <div style={{ padding: '12px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <span style={{ fontSize: '11px', opacity: 0.7, textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                  Source Audio
                </span>
                <div style={{ fontSize: `${hudFontSize}px`, color: '#F1F5F9' }}>
                  {isSimulating ? 'வணக்கம் மாணவர்களே, அனைவரும் புத்தகத்தைத் திறக்கவும்.' : 'Stream paused.'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '11px', opacity: 0.7, textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                  Translated Subtitles
                </span>
                <div style={{ fontSize: `${hudFontSize + 2}px`, fontWeight: 700, color: '#38BDF8' }}>
                  {isSimulating ? 'നമസ്കാരം വിദ്യാർത്ഥികളേ, എല്ലാവരും പുസ്തകം തുറക്കൂ.' : '--'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', opacity: 0.6, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '6px' }}>
              <span>Latency: 1.42s</span>
              <span>16kHz WebRTC VAD Active</span>
            </div>
          </div>
        </div>

        {/* Right Side: HUD Controls & Extension Instructions */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
            HUD Display Settings
          </h2>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Overlay Opacity</span>
              <span style={{ color: 'var(--text-secondary)' }}>{hudOpacity}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="100"
              value={hudOpacity}
              onChange={(e) => setHudOpacity(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Subtitle Font Size</span>
              <span style={{ color: 'var(--text-secondary)' }}>{hudFontSize}px</span>
            </div>
            <input
              type="range"
              min="12"
              max="24"
              value={hudFontSize}
              onChange={(e) => setHudFontSize(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
              Chrome Extension Integration
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              To inject this floating HUD directly into Google Meet or YouTube tabs, load the TRANSLARA Chrome Extension located in <code>/extension</code> into Developer Mode.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
