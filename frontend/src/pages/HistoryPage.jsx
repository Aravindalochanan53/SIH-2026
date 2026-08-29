import React, { useState } from 'react';
import { History, Mic, Video, MessageSquare, FileText, Trash2, Volume2, Copy, Check, Search, Bookmark } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export function HistoryPage() {
  const { savedTranslations } = useAppStore();
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const filteredHistory = savedTranslations
    .filter((h) => (filterType === 'all' ? true : h.type === filterType))
    .filter((h) => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        h.sourceText?.toLowerCase().includes(q) ||
        h.targetText?.toLowerCase().includes(q) ||
        h.sourceLang?.toLowerCase().includes(q) ||
        h.targetLang?.toLowerCase().includes(q)
      );
    });

  const getIcon = (type) => {
    switch (type) {
      case 'voice':
        return <Mic size={15} color="var(--primary)" />;
      case 'video':
        return <Video size={15} color="#7C3AED" />;
      case 'chat':
        return <MessageSquare size={15} color="#0D9488" />;
      case 'saved':
        return <Bookmark size={15} color="#EA580C" />;
      default:
        return <FileText size={15} color="var(--primary)" />;
    }
  };

  const handleCopy = async (id, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {}
  };

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
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Translation & Activity History
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Review recent text translations, voice sessions, classroom video jobs, and pedagogy chats
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'var(--bg-surface-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '6px 12px', width: '100%', maxWidth: '320px' }}>
          <Search size={15} color="var(--text-secondary)" />
          <input
            type="text"
            placeholder="Search history items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '13px', width: '100%', color: 'var(--text-primary)' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'all', label: 'All Activity' },
            { id: 'text', label: 'Text' },
            { id: 'voice', label: 'Voice' },
            { id: 'video', label: 'Video' },
            { id: 'chat', label: 'AI Chat' },
            { id: 'saved', label: 'Saved' },
          ].map((tab) => (
            <button
              key={tab.id}
              className="icon-action-btn"
              style={{
                fontSize: '12px',
                padding: '5px 12px',
                backgroundColor: filterType === tab.id ? 'var(--primary-light)' : 'var(--bg-surface)',
                borderColor: filterType === tab.id ? 'var(--primary)' : 'var(--border-color)',
                color: filterType === tab.id ? 'var(--primary)' : 'var(--text-primary)',
                fontWeight: filterType === tab.id ? 700 : 500,
              }}
              onClick={() => setFilterType(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* History Items List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredHistory.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <History size={36} color="var(--text-dim)" style={{ margin: '0 auto 10px auto' }} />
            <p>No activity found in this category.</p>
          </div>
        ) : (
          filteredHistory.map((item) => (
            <div key={item.id} className="white-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', flex: 1, minWidth: '260px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--bg-surface-secondary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {getIcon(item.type)}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="model-badge" style={{ fontWeight: 700 }}>
                      {item.sourceLang?.toUpperCase() || 'EN'} → {item.targetLang?.toUpperCase() || 'TA'}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.date}</span>
                  </div>

                  <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    "{item.sourceText}"
                  </div>

                  <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    "{item.targetText}"
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => handlePlay(item.targetText, item.targetLang || 'ml')}
                  className="icon-action-btn"
                  title="Listen"
                  style={{ padding: '6px 10px' }}
                >
                  <Volume2 size={14} />
                  <span>Listen</span>
                </button>
                <button
                  onClick={() => handleCopy(item.id, item.targetText)}
                  className="icon-action-btn"
                  title="Copy"
                  style={{ padding: '6px 10px' }}
                >
                  {copiedId === item.id ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                  <span>{copiedId === item.id ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
