import React from 'react';
import { Search, Sparkles, Globe } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from './LanguageSelector';

export function Navbar() {
  const {
    sourceLang,
    targetLang,
    setSourceLang,
    setTargetLang,
    swapLanguages,
    setActiveTab,
    capabilities,
  } = useAppStore();

  const isPairActive =
    capabilities?.languages?.[sourceLang]?.translation &&
    capabilities?.languages?.[targetLang]?.translation;

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <div className="search-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search lessons, phrases, worksheets..."
            className="search-input"
          />
        </div>
      </div>

      <div className="navbar-right">
        <div className="pair-status-badge">
          <span className={`status-dot ${isPairActive !== false ? 'green' : 'yellow'}`}></span>
          <span className="pair-text">
            {sourceLang.toUpperCase()} ⇄ {targetLang.toUpperCase()}
          </span>
        </div>

        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />

        <button
          className="demo-launch-btn"
          onClick={() => setActiveTab('video')}
          title="Instant SIH Demo"
        >
          <Sparkles size={15} />
          <span>Demo Video</span>
        </button>
      </div>
    </header>
  );
}
