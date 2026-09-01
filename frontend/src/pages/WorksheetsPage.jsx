import React, { useState } from 'react';
import { FileText, Download, CheckCircle, Sparkles, Layers, BookOpen, Hash, ArrowRight } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';
import { generateNumeracyWorksheet, generateLiteracyWorksheet, generateFlashcards } from '../api';

export function WorksheetsPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();

  const [selectedGrade, setSelectedGrade] = useState(1);
  const [selectedType, setSelectedType] = useState('numeracy'); // 'numeracy' | 'literacy' | 'flashcards'
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setDownloadUrl(null);
    try {
      let res;
      if (selectedType === 'numeracy') {
        res = await generateNumeracyWorksheet(sourceLang, targetLang, selectedGrade);
      } else if (selectedType === 'literacy') {
        res = await generateLiteracyWorksheet(sourceLang, targetLang, selectedGrade);
      } else {
        res = await generateFlashcards(sourceLang, targetLang);
      }
      setDownloadUrl(`http://localhost:8000${res.download_url}`);
      window.open(`http://localhost:8000${res.download_url}`, '_blank');
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Worksheet & Pedagogy Studio
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Create printable NIPUN Bharat aligned bilingual worksheets and flashcards for primary classrooms
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

      {/* Configuration Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Left: Configuration Wizard */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
            Worksheet Configuration Wizard
          </h2>

          {/* Step 1: Grade Selection */}
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
              1. Target Primary Grade
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              {[1, 2, 3].map((g) => (
                <button
                  key={`grade-${g}`}
                  className={`icon-action-btn ${selectedGrade === g ? 'selected' : ''}`}
                  style={{
                    flex: 1,
                    justifyContent: 'center',
                    backgroundColor: selectedGrade === g ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                    borderColor: selectedGrade === g ? 'var(--primary)' : 'var(--border-color)',
                    color: selectedGrade === g ? 'var(--primary)' : 'var(--text-primary)',
                    fontWeight: selectedGrade === g ? 700 : 500,
                  }}
                  onClick={() => setSelectedGrade(g)}
                >
                  Grade {g}
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Activity Type */}
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
              2. Pedagogy Activity Type
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { id: 'numeracy', title: 'Numeracy Counting Worksheet', desc: 'Dot counting, numerals, and tracing exercises' },
                { id: 'literacy', title: 'Bilingual Literacy Matching Worksheet', desc: 'Picture and vocabulary connecting lines' },
                { id: 'flashcards', title: '2x4 Bilingual Vocabulary Flashcards', desc: 'Printable cut-out cards with native script and pronunciation' },
              ].map((item) => (
                <div
                  key={item.id}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${selectedType === item.id ? 'var(--primary)' : 'var(--border-color)'}`,
                    backgroundColor: selectedType === item.id ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                    cursor: 'pointer',
                  }}
                  onClick={() => setSelectedType(item.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="radio"
                      checked={selectedType === item.id}
                      onChange={() => setSelectedType(item.id)}
                      id={`radio-${item.id}`}
                    />
                    <label htmlFor={`radio-${item.id}`} style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}>
                      {item.title}
                    </label>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', marginLeft: '24px' }}>
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Generate Button */}
          <button
            className="primary-action-btn"
            onClick={handleGenerate}
            disabled={isGenerating}
            style={{ width: '100%', justifyContent: 'center', padding: '12px', marginTop: '8px' }}
          >
            {isGenerating ? (
              <>
                <span className="dot-flashing" />
                <span>Generating High-Resolution PDF...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Generate & Download Worksheet PDF</span>
              </>
            )}
          </button>
        </div>

        {/* Right: Live Preview Panel */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
            Live Worksheet Preview
          </h2>

          <div style={{ flex: 1, border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '20px', backgroundColor: 'var(--bg-surface-secondary)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ textAlign: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase' }}>
                NIPUN BHARAT PRIMARY EDUCATION INITIATIVE
              </span>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                {selectedType === 'numeracy'
                  ? `Grade ${selectedGrade} Bilingual Numeracy Worksheet`
                  : selectedType === 'literacy'
                  ? `Grade ${selectedGrade} Bilingual Matching Worksheet`
                  : 'Bilingual Vocabulary Flashcards'}
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {sourceLang.toUpperCase()} ⇄ {targetLang.toUpperCase()}
              </span>
            </div>

            {/* Sample items */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
              {[
                { word: 'Book', src: 'புத்தகம்', tgt: 'പുസ്തകം' },
                { word: 'Pen', src: 'எழுதுகோல்', tgt: 'പേന' },
                { word: 'School', src: 'பள்ளி', tgt: 'സ്കൂൾ' },
                { word: 'Teacher', src: 'ஆசிரியர்', tgt: 'അധ്യാപകൻ' },
              ].map((item, idx) => (
                <div key={`prev-${idx}`} style={{ padding: '10px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.word}</span>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>{item.src}</div>
                  <div style={{ fontSize: '13px', color: 'var(--primary)', marginTop: '2px' }}>{item.tgt}</div>
                </div>
              ))}
            </div>

            {downloadUrl && (
              <div style={{ marginTop: 'auto', paddingTop: '12px', textAlign: 'center' }}>
                <a
                  href={downloadUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="primary-action-btn"
                  style={{ textDecoration: 'none', display: 'inline-flex' }}
                >
                  <Download size={15} />
                  <span>Download Generated PDF</span>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
