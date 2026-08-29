import React, { useState, useEffect } from 'react';
import { WifiOff, Search, Volume2, CheckCircle2, ShieldCheck, RefreshCw, Globe2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { getCachedPhrases } from '../api';

export function OfflinePage() {
  const { isSimulatedOffline, setSimulatedOffline } = useAppStore();
  const [phrases, setPhrases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCat, setSelectedCat] = useState('all');

  useEffect(() => {
    getCachedPhrases().then(setPhrases).catch(console.error);
  }, []);

  const categories = ['all', 'classroom_instructions', 'greetings', 'courtesy', 'numbers'];

  const filteredPhrases = phrases.filter((p) => {
    const matchesCat = selectedCat === 'all' || p.category === selectedCat;
    const matchesSearch =
      searchTerm === '' ||
      p.source_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.target_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.pronunciation?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const handlePlay = (text, lang) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      const langMap = { en: 'en-US', ta: 'ta-IN', ml: 'ml-IN', te: 'te-IN', kn: 'kn-IN', hi: 'hi-IN' };
      u.lang = langMap[lang] || 'en-US';
      window.speechSynthesis.speak(u);
    }
  };

  return (
    <div className="page-container">
      {/* Offline Mode Banner */}
      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', backgroundColor: isSimulatedOffline ? 'var(--warning-light)' : 'var(--primary-light)', color: isSimulatedOffline ? 'var(--warning-text)' : 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <WifiOff size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              Offline Classroom Phrase Library
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Verified educational phrases stored locally in SQLite database for zero-latency offline operation
            </p>
          </div>
        </div>

        {/* Mode Toggle Button */}
        <button
          className="icon-action-btn"
          style={{
            backgroundColor: isSimulatedOffline ? 'var(--warning-light)' : 'var(--bg-surface)',
            borderColor: isSimulatedOffline ? 'var(--warning-border)' : 'var(--border-color)',
            color: isSimulatedOffline ? 'var(--warning-text)' : 'var(--text-primary)',
            fontWeight: 600,
            padding: '8px 16px',
          }}
          onClick={() => setSimulatedOffline(!isSimulatedOffline)}
        >
          <span>{isSimulatedOffline ? 'Offline Mode Active' : 'Online AI Mode'}</span>
        </button>
      </div>

      {/* Search & Category Filter Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'var(--bg-surface-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '6px 12px', width: '100%', maxWidth: '340px' }}>
          <Search size={15} color="var(--text-secondary)" />
          <input
            type="text"
            placeholder="Search offline phrases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '13px', width: '100%', color: 'var(--text-primary)' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {categories.map((cat) => (
            <button
              key={`cat-${cat}`}
              className="icon-action-btn"
              style={{
                textTransform: 'capitalize',
                fontSize: '12px',
                padding: '5px 12px',
                backgroundColor: selectedCat === cat ? 'var(--primary-light)' : 'var(--bg-surface)',
                borderColor: selectedCat === cat ? 'var(--primary)' : 'var(--border-color)',
                color: selectedCat === cat ? 'var(--primary)' : 'var(--text-primary)',
                fontWeight: selectedCat === cat ? 700 : 500,
              }}
              onClick={() => setSelectedCat(cat)}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Phrases Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
        {filteredPhrases.map((phrase) => (
          <div key={phrase.id} className="white-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="model-badge" style={{ textTransform: 'capitalize' }}>
                {phrase.category.replace('_', ' ')}
              </span>
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={13} />
                <span>Verified</span>
              </span>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '2px' }}>
                Source ({phrase.source_language?.toUpperCase() || 'TA'})
              </div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {phrase.source_text}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--primary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '2px' }}>
                Target ({phrase.target_language?.toUpperCase() || 'ML'})
              </div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary)' }}>
                {phrase.target_text}
              </div>
              {phrase.pronunciation && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {phrase.pronunciation}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                onClick={() => handlePlay(phrase.target_text, phrase.target_language || 'ml')}
                className="icon-action-btn"
                style={{ padding: '4px 10px', fontSize: '12px' }}
                title="Play Audio"
              >
                <Volume2 size={13} />
                <span>Play</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
