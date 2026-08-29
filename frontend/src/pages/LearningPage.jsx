import React, { useState } from 'react';
import { BookOpen, Volume2, RotateCw, Sparkles, Download, ArrowRight } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';
import { generateFlashcards } from '../api';

export function LearningPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();
  const [flippedIndex, setFlippedIndex] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [isGenerating, setIsGenerating] = useState(false);

  const flashcardsData = [
    {
      id: 1,
      category: 'classroom',
      english: 'Book',
      sourceText: 'புத்தகம்',
      targetText: 'പുസ്തകം',
      sourcePronun: 'Puthagam',
      targetPronun: 'Pusthakam',
    },
    {
      id: 2,
      category: 'classroom',
      english: 'Pen / Pencil',
      sourceText: 'எழுதுகோல்',
      targetText: 'പേന',
      sourcePronun: 'Ezhuthukol',
      targetPronun: 'Pena',
    },
    {
      id: 3,
      category: 'classroom',
      english: 'School',
      sourceText: 'பள்ளி',
      targetText: 'സ്കൂൾ',
      sourcePronun: 'Palli',
      targetPronun: 'School',
    },
    {
      id: 4,
      category: 'numbers',
      english: 'One (1)',
      sourceText: 'ஒன்று (1)',
      targetText: 'ഒന്ന് (1)',
      sourcePronun: 'Ondru',
      targetPronun: 'Onnu',
    },
    {
      id: 5,
      category: 'numbers',
      english: 'Two (2)',
      sourceText: 'இரண்டு (2)',
      targetText: 'രണ്ട് (2)',
      sourcePronun: 'Irandu',
      targetPronun: 'Randu',
    },
    {
      id: 6,
      category: 'numbers',
      english: 'Three (3)',
      sourceText: 'மூன்று (3)',
      targetText: 'മൂന്ന് (3)',
      sourcePronun: 'Moondru',
      targetPronun: 'Moonnu',
    },
    {
      id: 7,
      category: 'greetings',
      english: 'Hello / Greetings',
      sourceText: 'வணக்கம்',
      targetText: 'നമസ്കാരം',
      sourcePronun: 'Vanakkam',
      targetPronun: 'Namaskaram',
    },
    {
      id: 8,
      category: 'greetings',
      english: 'Thank you',
      sourceText: 'நன்றி',
      targetText: 'നന്ദി',
      sourcePronun: 'Nandri',
      targetPronun: 'Nandi',
    },
  ];

  const categories = ['all', 'classroom', 'numbers', 'greetings'];

  const filteredCards = flashcardsData.filter((card) => {
    if (activeCategory === 'all') return true;
    return card.category === activeCategory;
  });

  const handleDownloadPDF = async () => {
    setIsGenerating(true);
    try {
      const res = await generateFlashcards(sourceLang, targetLang);
      window.open(`http://localhost:8000${res.download_url}`, '_blank');
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlayTTS = (e, text, lang) => {
    e.stopPropagation();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const langMap = { en: 'en-US', ta: 'ta-IN', ml: 'ml-IN', te: 'te-IN', kn: 'kn-IN', hi: 'hi-IN' };
      utterance.lang = langMap[lang] || 'en-US';
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Interactive Flashcards & Vocabulary
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            Foundational vocabulary flashcards with interactive 3D flips and native pronunciation
          </p>
        </div>

        <button
          className="primary-action-btn"
          onClick={handleDownloadPDF}
          disabled={isGenerating}
        >
          <Download size={15} />
          <span>{isGenerating ? 'Generating PDF...' : 'Download Printable PDF'}</span>
        </button>
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

      {/* Category Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {categories.map((cat) => (
          <button
            key={`cat-${cat}`}
            className="icon-action-btn"
            style={{
              textTransform: 'capitalize',
              backgroundColor: activeCategory === cat ? 'var(--primary-light)' : 'var(--bg-surface)',
              borderColor: activeCategory === cat ? 'var(--primary)' : 'var(--border-color)',
              color: activeCategory === cat ? 'var(--primary)' : 'var(--text-primary)',
              fontWeight: activeCategory === cat ? 700 : 500,
            }}
            onClick={() => setActiveCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Flashcards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
        {filteredCards.map((card, idx) => {
          const isFlipped = flippedIndex === card.id;
          return (
            <div
              key={card.id}
              className="white-card"
              style={{
                cursor: 'pointer',
                minHeight: '190px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease',
                backgroundColor: isFlipped ? 'var(--primary-light)' : 'var(--bg-surface)',
                borderColor: isFlipped ? 'var(--primary-border)' : 'var(--border-color)',
              }}
              onClick={() => setFlippedIndex(isFlipped ? null : card.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="model-badge" style={{ textTransform: 'uppercase' }}>
                  {card.category}
                </span>
                <button
                  style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                  onClick={(e) => { e.stopPropagation(); setFlippedIndex(isFlipped ? null : card.id); }}
                >
                  <RotateCw size={12} />
                  <span>Flip</span>
                </button>
              </div>

              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  {card.english}
                </span>
                <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {isFlipped ? card.targetText : card.sourceText}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--primary)', marginTop: '4px' }}>
                  {isFlipped ? card.targetPronun : card.sourcePronun}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                <span>{isFlipped ? `Target: ${targetLang.toUpperCase()}` : `Source: ${sourceLang.toUpperCase()}`}</span>
                <button
                  onClick={(e) => handlePlayTTS(e, isFlipped ? card.targetText : card.sourceText, isFlipped ? targetLang : sourceLang)}
                  className="icon-action-btn"
                  style={{ padding: '3px 8px', fontSize: '11px' }}
                  title="Listen Pronunciation"
                >
                  <Volume2 size={13} />
                  <span>Listen</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
