import React, { useState } from 'react';
import { FileText, Download, Sparkles, BookOpen, Layers } from 'lucide-react';
import { generateFlashcards, generateLiteracyWorksheet, generateNumeracyWorksheet } from '../api';

export function WorksheetPanel({ sourceLang, targetLang }) {
  const [loading, setLoading] = useState(false);
  const [lastGenerated, setLastGenerated] = useState(null);

  const handleGenerate = async (type) => {
    setLoading(true);
    setLastGenerated(null);
    try {
      let res;
      if (type === 'flashcards') {
        res = await generateFlashcards(sourceLang, targetLang);
      } else if (type === 'numeracy') {
        res = await generateNumeracyWorksheet(sourceLang, targetLang, 1);
      } else {
        res = await generateLiteracyWorksheet(sourceLang, targetLang, 1);
      }
      setLastGenerated(res);
      window.open(`http://localhost:8000${res.download_url}`, '_blank');
    } catch (err) {
      console.error('PDF Generation Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <BookOpen size={16} color="var(--primary)" />
            <span>Pedagogy & Worksheet Studio</span>
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Generate bilingual printable classroom materials
          </p>
        </div>
        {loading && <span className="model-badge">Generating PDF...</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        <div style={{ padding: '14px', backgroundColor: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Vocabulary Flashcards
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Bilingual flashcards with pronunciation and native scripts.
          </p>
          <button
            className="icon-action-btn"
            disabled={loading}
            onClick={() => handleGenerate('flashcards')}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Download size={14} />
            <span>Download Flashcards</span>
          </button>
        </div>

        <div style={{ padding: '14px', backgroundColor: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Numeracy Worksheet
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Counting exercises, handwriting numbers, and visual math.
          </p>
          <button
            className="icon-action-btn"
            disabled={loading}
            onClick={() => handleGenerate('numeracy')}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Download size={14} />
            <span>Download Numeracy PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
}
