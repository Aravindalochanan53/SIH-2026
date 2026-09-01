import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Volume2,
  Copy,
  Check,
  RotateCcw,
  Bookmark,
  Sparkles,
  ArrowRight,
  Video,
  MessageSquare,
  BookOpen,
  FileText,
  Radio,
  ClipboardPaste,
  Trash2,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';
import { translateText } from '../api';

export function HomePage() {
  const {
    sourceLang,
    targetLang,
    setSourceLang,
    setTargetLang,
    swapLanguages,
    addHistoryItem,
    isSimulatedOffline,
  } = useAppStore();

  const [inputText, setInputText] = useState('வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?');
  const [outputText, setOutputText] = useState('നമസ്കാരം, സുഖമാണോ?');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [micError, setMicError] = useState(null);

  const recognitionRef = useRef(null);
  const timerRef = useRef(null);

  // Quick sample prompts
  const samplePrompts = [
    { text: 'வணக்கம்', src: 'ta', tgt: 'ml' },
    { text: 'Hello, how are you?', src: 'en', tgt: 'ta' },
    { text: 'Open your book.', src: 'en', tgt: 'ml' },
    { text: 'இன்று நாம் 1 முதல் 10 வரை எண்களைக் கற்றுக்கொள்வோம்.', src: 'ta', tgt: 'en' },
    { text: 'Good morning students, please sit down.', src: 'en', tgt: 'hi' },
  ];

  // Perform translation
  const handleTranslate = async (textToTranslate = inputText) => {
    if (!textToTranslate.trim() || isLoading) return;
    setIsLoading(true);
    setCopied(false);
    setSaved(false);

    try {
      const res = await translateText(textToTranslate.trim(), sourceLang, targetLang);
      const translated = res.translation || res.translated_text || res.target_text || '';
      setOutputText(translated);

      if (translated) {
        addHistoryItem({
          id: `h_${Date.now()}`,
          type: 'text',
          sourceLang,
          targetLang,
          sourceText: textToTranslate.trim(),
          targetText: translated,
          date: 'Just now',
        });
      }
    } catch (err) {
      console.error('Translation error:', err);
      setOutputText(`[Translation Error: ${err.message}]`);
    } finally {
      setIsLoading(false);
    }
  };

  // Copy to clipboard
  const handleCopy = async () => {
    if (!outputText) return;
    try {
      await navigator.clipboard.writeText(outputText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Copy failed:', e);
    }
  };

  // Save to history
  const handleSave = () => {
    if (!outputText) return;
    addHistoryItem({
      id: `saved_${Date.now()}`,
      type: 'saved',
      sourceLang,
      targetLang,
      sourceText: inputText,
      targetText: outputText,
      date: 'Saved item',
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  // Text-To-Speech Playback
  const handlePlayTTS = () => {
    if (!outputText) return;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(outputText);
      const langMap = {
        en: 'en-US', ta: 'ta-IN', ml: 'ml-IN',
        te: 'te-IN', kn: 'kn-IN', hi: 'hi-IN',
      };
      utterance.lang = langMap[targetLang] || 'en-US';
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Paste from clipboard
  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setInputText(text);
    } catch (err) {
      console.warn('Clipboard read notice:', err);
    }
  };

  // Microphone
  const handleToggleMic = async () => {
    setMicError(null);
    if (isRecording) {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      clearInterval(timerRef.current);
      setIsRecording(false);
      setRecordingSeconds(0);
    } else {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = false;
          rec.interimResults = true;
          const langMap = { en: 'en-US', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN', ml: 'ml-IN', hi: 'hi-IN' };
          rec.lang = langMap[sourceLang] || 'en-US';
          rec.onstart = () => {
            setIsRecording(true);
            setRecordingSeconds(0);
            timerRef.current = setInterval(() => setRecordingSeconds((s) => s + 1), 1000);
          };
          rec.onresult = (event) => {
            const transcript = Array.from(event.results).map((r) => r[0].transcript).join('');
            setInputText(transcript);
          };
          rec.onerror = (e) => {
            if (e.error === 'not-allowed') setMicError('Microphone permission required.');
            setIsRecording(false);
            clearInterval(timerRef.current);
          };
          rec.onend = () => { setIsRecording(false); clearInterval(timerRef.current); };
          recognitionRef.current = rec;
          rec.start();
        } catch (e) {
          setMicError('Speech recognition not available.');
        }
      } else {
        setMicError('Speech recognition not supported in this browser.');
      }
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recognitionRef.current) { try { recognitionRef.current.stop(); } catch (e) {} }
    };
  }, []);

  const formatSeconds = (sec) => {
    const mins = Math.floor(sec / 60);
    const s = sec % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="page-container animate-fade-in">
      {/* Hero Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
              TRANSLARA
            </h1>
            <span style={{
              fontSize: '11px', fontWeight: 700, padding: '2px 10px',
              borderRadius: 'var(--radius-full)', background: 'var(--primary-light)',
              color: 'var(--primary)', border: '1px solid var(--primary-border)',
            }}>
              AI Multilingual Classroom
            </span>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            AI-powered real-time multilingual translation and vernacular learning platform
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/voice" className="icon-action-btn" style={{ textDecoration: 'none', fontWeight: 600 }}>
            <Radio size={15} color="var(--primary)" />
            <span>Live Speech</span>
          </Link>
          <Link to="/video" className="icon-action-btn" style={{ textDecoration: 'none', fontWeight: 600 }}>
            <Video size={15} color="var(--accent-purple)" />
            <span>Video Translate</span>
          </Link>
        </div>
      </div>

      {/* Main Translation Workspace */}
      <div className="glass-panel" style={{ padding: '26px' }}>
        {/* Language Selection Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <LanguageSelector
            sourceLang={sourceLang}
            targetLang={targetLang}
            onSourceChange={setSourceLang}
            onTargetChange={setTargetLang}
            onSwap={swapLanguages}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="model-badge indic">
              <Sparkles size={12} />
              <span>IndicTrans2 NMT</span>
            </span>
            {isSimulatedOffline && (
              <span className="model-badge" style={{ background: 'var(--warning-light)', color: 'var(--warning-text)', borderColor: 'var(--warning-border)' }}>
                Offline Cache Active
              </span>
            )}
          </div>
        </div>

        {micError && (
          <div className="form-error" style={{ marginBottom: '16px' }}>
            <span>{micError}</span>
          </div>
        )}

        {/* Dual Translation Workspace Grid */}
        <div className="translation-deck-grid">
          {/* SOURCE INPUT CARD */}
          <div className="translation-card">
            <div className="card-top-bar">
              <span className="card-label-tag">Source Text</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button className="icon-action-btn" onClick={handlePaste} title="Paste" style={{ padding: '4px 8px', fontSize: '12px' }}>
                  <ClipboardPaste size={13} /> <span>Paste</span>
                </button>
                {inputText && (
                  <button className="icon-action-btn" onClick={() => setInputText('')} title="Clear" style={{ padding: '4px 8px', fontSize: '12px' }}>
                    <Trash2 size={13} /> <span>Clear</span>
                  </button>
                )}
              </div>
            </div>

            <textarea
              className="input-textarea"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Type or speak your message in English or any Indian language..."
              rows={4}
            />

            <div className="card-bottom-bar">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button
                  className={`mic-action-btn ${isRecording ? 'stop' : 'start'}`}
                  onClick={handleToggleMic}
                  style={{ padding: '6px 14px', fontSize: '13px' }}
                >
                  {isRecording ? <MicOff size={15} /> : <Mic size={15} />}
                  <span>{isRecording ? `● Recording ${formatSeconds(recordingSeconds)}` : 'Speak'}</span>
                </button>
                <span className="char-counter">{inputText.length} chars</span>
              </div>

              <button
                className="primary-action-btn"
                onClick={() => handleTranslate()}
                disabled={isLoading || !inputText.trim()}
              >
                {isLoading ? (
                  <><span className="dot-flashing" /><span>Translating...</span></>
                ) : (
                  <><span>Translate</span><ArrowRight size={15} /></>
                )}
              </button>
            </div>
          </div>

          {/* SWAP */}
          <div className="swap-column">
            <button className="swap-circle-btn" onClick={swapLanguages} title="Swap Languages" aria-label="Swap Languages">
              ⇄
            </button>
          </div>

          {/* TARGET OUTPUT CARD */}
          <div className="translation-card" style={{ background: 'var(--bg-surface-secondary)' }}>
            <div className="card-top-bar">
              <span className="card-label-tag">Translation Output</span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                {targetLang.toUpperCase()}
              </span>
            </div>

            <div className="output-text-area">
              {outputText ? outputText : (
                <span className="output-placeholder">
                  {isLoading ? 'Generating translation...' : 'Translation will appear here...'}
                </span>
              )}
            </div>

            <div className="card-bottom-bar">
              <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                {outputText ? 'Translated via IndicTrans2' : 'Ready'}
              </span>
              <div className="action-buttons-group">
                <button className="icon-action-btn" onClick={handlePlayTTS} disabled={!outputText} title="Listen">
                  <Volume2 size={15} /> <span>Listen</span>
                </button>
                <button className="icon-action-btn" onClick={handleCopy} disabled={!outputText} title="Copy">
                  {copied ? <Check size={15} color="var(--success)" /> : <Copy size={15} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button className="icon-action-btn" onClick={handleSave} disabled={!outputText} title="Save">
                  <Bookmark size={15} color={saved ? 'var(--primary)' : 'currentColor'} />
                  <span>{saved ? 'Saved' : 'Save'}</span>
                </button>
                <button className="icon-action-btn" onClick={() => handleTranslate()} disabled={isLoading || !inputText.trim()} title="Re-translate">
                  <RotateCcw size={14} /> <span>Re-translate</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sample Prompts */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '8px' }}>
            Quick Classroom Examples:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {samplePrompts.map((p, idx) => (
              <button
                key={`sample-${idx}`}
                className="icon-action-btn"
                style={{ fontSize: '12px', padding: '5px 10px' }}
                onClick={() => {
                  setSourceLang(p.src);
                  setTargetLang(p.tgt);
                  setInputText(p.text);
                  handleTranslate(p.text);
                }}
              >
                <span>{p.src.toUpperCase()} → {p.tgt.toUpperCase()}:</span>
                <span style={{ fontWeight: 600 }}>"{p.text}"</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Quick Links */}
      <div className="feature-cards-grid">
        <Link to="/voice" className="feature-card">
          <div className="feature-card-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.12)', color: '#10B981' }}>
            <Mic size={20} />
          </div>
          <div className="feature-card-title">Live Speech</div>
          <div className="feature-card-desc">Real-time classroom translation with zero-jitter streaming.</div>
        </Link>
        <Link to="/video" className="feature-card">
          <div className="feature-card-icon" style={{ backgroundColor: 'rgba(139, 92, 246, 0.12)', color: '#8B5CF6' }}>
            <Video size={20} />
          </div>
          <div className="feature-card-title">Video Translate</div>
          <div className="feature-card-desc">Generate dual subtitles and voice dubbing for lectures.</div>
        </Link>
        <Link to="/chat" className="feature-card">
          <div className="feature-card-icon" style={{ backgroundColor: 'rgba(6, 182, 212, 0.12)', color: '#06B6D4' }}>
            <MessageSquare size={20} />
          </div>
          <div className="feature-card-title">TRANSLARA AI</div>
          <div className="feature-card-desc">Multilingual concept explanations and lesson planning.</div>
        </Link>
        <Link to="/worksheets" className="feature-card">
          <div className="feature-card-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.12)', color: '#F59E0B' }}>
            <FileText size={20} />
          </div>
          <div className="feature-card-title">Worksheets</div>
          <div className="feature-card-desc">Bilingual printable flashcards and literacy worksheets.</div>
        </Link>
      </div>
    </div>
  );
}
