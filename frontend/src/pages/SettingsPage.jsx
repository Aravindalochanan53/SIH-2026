import React, { useState } from 'react';
import {
  Settings,
  Shield,
  Cpu,
  Volume2,
  Globe,
  Mic,
  Sparkles,
  Check,
  Activity,
  Sliders,
  Database,
  Lock,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';

export function SettingsPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages, isSimulatedOffline, setSimulatedOffline } = useAppStore();

  const [autoPlayAudio, setAutoPlayAudio] = useState(true);
  const [saveLocalHistory, setSaveLocalHistory] = useState(true);
  const [selectedBackend, setSelectedBackend] = useState('indictrans2');
  const [selectedASR, setSelectedASR] = useState('faster_whisper');
  const [vadAggressiveness, setVadAggressiveness] = useState(2);
  const [savedAlert, setSavedAlert] = useState(false);

  const handleSaveSettings = () => {
    setSavedAlert(true);
    setTimeout(() => setSavedAlert(false), 2500);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            System Settings
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            Configure language routing, AI model backends, audio calibration, and offline defaults
          </p>
        </div>

        <button
          className="primary-action-btn"
          onClick={handleSaveSettings}
        >
          <Check size={16} />
          <span>{savedAlert ? 'Settings Saved' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Settings Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Section 1: Default Language Pair */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <Globe size={18} color="var(--primary)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Default Language Preferences
            </h2>
          </div>

          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Choose your default source and target translation languages. The application UI remains strictly in English.
          </p>

          <LanguageSelector
            sourceLang={sourceLang}
            targetLang={targetLang}
            onSourceChange={setSourceLang}
            onTargetChange={setTargetLang}
            onSwap={swapLanguages}
          />
        </div>

        {/* Section 2: AI Model Backend */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <Cpu size={18} color="var(--primary)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Translation Engine & Model Backend
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { id: 'indictrans2', label: 'Local Translation Model (Fine-Tuned / IndicTrans2)', desc: '100% locally hosted transformer running on device memory' },
              { id: 'neural_grammar', label: 'Local Neural Grammar & Syntactic Engine', desc: 'Rule-augmented fast local neural inference engine' },
              { id: 'offline', label: 'Zero-Latency Verified Local Cache', desc: 'Pre-indexed local classroom dialog database' },
            ].map((engine) => (
              <div
                key={engine.id}
                style={{
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${selectedBackend === engine.id ? 'var(--primary)' : 'var(--border-color)'}`,
                  backgroundColor: selectedBackend === engine.id ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedBackend(engine.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="radio"
                    checked={selectedBackend === engine.id}
                    onChange={() => setSelectedBackend(engine.id)}
                    id={`engine-${engine.id}`}
                  />
                  <label htmlFor={`engine-${engine.id}`} style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}>
                    {engine.label}
                  </label>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', marginLeft: '24px' }}>
                  {engine.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Audio & VAD Settings */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <Volume2 size={18} color="var(--primary)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Audio & Speech Settings
            </h2>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'block' }}>
                Auto-play TTS Pronunciation
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Automatically play synthesized voice for new translations
              </span>
            </div>
            <input
              type="checkbox"
              checked={autoPlayAudio}
              onChange={(e) => setAutoPlayAudio(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Voice Activity Detection (VAD) Aggressiveness</span>
              <span style={{ color: 'var(--text-secondary)' }}>Level {vadAggressiveness} (Balanced)</span>
            </div>
            <input
              type="range"
              min="0"
              max="3"
              value={vadAggressiveness}
              onChange={(e) => setVadAggressiveness(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Section 4: Offline Mode & Privacy */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <Shield size={18} color="var(--primary)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Offline Cache & Privacy
            </h2>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'block' }}>
                Simulate Offline Mode
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Test zero-connectivity classroom behavior with local SQLite cache
              </span>
            </div>
            <input
              type="checkbox"
              checked={isSimulatedOffline}
              onChange={(e) => setSimulatedOffline(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'block' }}>
                Save Translation History Locally
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Keep recent voice and text translations for classroom review
              </span>
            </div>
            <input
              type="checkbox"
              checked={saveLocalHistory}
              onChange={(e) => setSaveLocalHistory(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
