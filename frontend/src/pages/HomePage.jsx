import React, { useState, useEffect, useRef } from 'react';
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
  Globe2,
  ShieldCheck,
  Zap,
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
    setActiveTab,
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
      // Fallback display
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
      // Map standard language codes
      const langMap = {
        en: 'en-US',
        ta: 'ta-IN',
        ml: 'ml-IN',
        te: 'te-IN',
        kn: 'kn-IN',
        hi: 'hi-IN',
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
      if (text) {
        setInputText(text);
      }
    } catch (err) {
      console.warn('Clipboard read notice:', err);
    }
  };

  // Real Microphone Audio Capture via Web Speech API / getUserMedia
  const handleToggleMic = async () => {
    setMicError(null);

    if (isRecording) {
      // Stop recording
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
      clearInterval(timerRef.current);
      setIsRecording(false);
      setRecordingSeconds(0);
    } else {
      // Start recording
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = false;
          rec.interimResults = true;

          const langMap = {
            en: 'en-US',
            ta: 'ta-IN',
            te: 'te-IN',
            kn: 'kn-IN',
            ml: 'ml-IN',
            hi: 'hi-IN',
          };
          rec.lang = langMap[sourceLang] || 'en-US';

          rec.onstart = () => {
            setIsRecording(true);
            setRecordingSeconds(0);
            timerRef.current = setInterval(() => {
              setRecordingSeconds((s) => s + 1);
            }, 1000);
          };

          rec.onresult = (event) => {
            const transcript = Array.from(event.results)
              .map((r) => r[0].transcript)
              .join('');
            setInputText(transcript);
          };

          rec.onerror = (e) => {
            console.error('Speech recognition notice:', e.error);
            if (e.error === 'not-allowed') {
              setMicError('Microphone permission required. Please allow microphone access in your browser.');
            }
            setIsRecording(false);
            clearInterval(timerRef.current);
          };

          rec.onend = () => {
            setIsRecording(false);
            clearInterval(timerRef.current);
          };

          recognitionRef.current = rec;
          rec.start();
        } catch (e) {
          console.warn('SpeechRecognition failed, falling back to getUserMedia:', e);
          startMediaStreamFallback();
        }
      } else {
        startMediaStreamFallback();
      }
    }
  };

  const startMediaStreamFallback = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1);
      }, 1000);

      setTimeout(() => {
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);
        clearInterval(timerRef.current);
      }, 5000);
    } catch (err) {
      setMicError('Microphone permission required. Please allow microphone access in your browser.');
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
    };
  }, []);

  const formatSeconds = (sec) => {
    const mins = Math.floor(sec / 60);
    const s = sec % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="page-container">
      {/* Hero Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
              TRANSLARA
            </h1>
            <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: 'var(--radius-full)', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', border: '1px solid var(--primary-border)' }}>
              AI Multilingual Classroom
            </span>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            AI-powered real-time multilingual translation and vernacular learning platform
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="icon-action-btn"
            onClick={() => setActiveTab('voice')}
            style={{ backgroundColor: 'var(--bg-surface)', fontWeight: 600 }}
          >
            <Radio size={15} color="var(--primary)" />
            <span>Live Speech</span>
          </button>
          <button
            className="icon-action-btn"
            onClick={() => setActiveTab('video')}
            style={{ backgroundColor: 'var(--bg-surface)', fontWeight: 600 }}
          >
            <Video size={15} color="#7C3AED" />
            <span>Video Translate</span>
          </button>
        </div>
      </div>

      {/* Main Translation Workspace */}
      <div className="glass-panel" style={{ padding: '24px' }}>
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
              <span className="model-badge" style={{ backgroundColor: 'var(--warning-light)', color: 'var(--warning-text)', borderColor: 'var(--warning-border)' }}>
                Offline Cache Active
              </span>
            )}
          </div>
        </div>

        {/* Microphone Notice Alert if error */}
        {micError && (
          <div className="offline-alert-banner" style={{ marginBottom: '16px', backgroundColor: 'var(--error-light)', borderColor: 'var(--error-border)', color: 'var(--error-text)' }}>
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
                <button
                  className="icon-action-btn"
                  onClick={handlePaste}
                  title="Paste from clipboard"
                  style={{ padding: '4px 8px', fontSize: '12px' }}
                >
                  <ClipboardPaste size={13} />
                  <span>Paste</span>
                </button>
                {inputText && (
                  <button
                    className="icon-action-btn"
                    onClick={() => setInputText('')}
                    title="Clear text"
                    style={{ padding: '4px 8px', fontSize: '12px' }}
                  >
                    <Trash2 size={13} />
                    <span>Clear</span>
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
                  <>
                    <span className="dot-flashing" />
                    <span>Translating...</span>
                  </>
                ) : (
                  <>
                    <span>Translate</span>
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* SWAP ICON COLUMN */}
          <div className="swap-column">
            <button
              className="swap-circle-btn"
              onClick={swapLanguages}
              title="Swap Source & Target Languages"
              aria-label="Swap Languages"
            >
              ⇄
            </button>
          </div>

          {/* TARGET OUTPUT CARD */}
          <div className="translation-card" style={{ backgroundColor: 'var(--bg-surface-secondary)' }}>
            <div className="card-top-bar">
              <span className="card-label-tag">Translation Output</span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                {targetLang.toUpperCase()}
              </span>
            </div>

            <div className="output-text-area">
              {outputText ? (
                outputText
              ) : (
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
                <button
                  className="icon-action-btn"
                  onClick={handlePlayTTS}
                  disabled={!outputText}
                  title="Listen to pronunciation"
                >
                  <Volume2 size={15} />
                  <span>Listen</span>
                </button>
                <button
                  className="icon-action-btn"
                  onClick={handleCopy}
                  disabled={!outputText}
                  title="Copy translation"
                >
                  {copied ? <Check size={15} color="var(--success)" /> : <Copy size={15} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button
                  className="icon-action-btn"
                  onClick={handleSave}
                  disabled={!outputText}
                  title="Save to history"
                >
                  <Bookmark size={15} color={saved ? 'var(--primary)' : 'currentColor'} />
                  <span>{saved ? 'Saved' : 'Save'}</span>
                </button>
                <button
                  className="icon-action-btn"
                  onClick={() => handleTranslate()}
                  disabled={isLoading || !inputText.trim()}
                  title="Re-translate"
                >
                  <RotateCcw size={14} />
                  <span>Re-translate</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sample Educational Phrases */}
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

      {/* Feature Modules Quick Links Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        <div
          className="white-card"
          style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
          onClick={() => setActiveTab('voice')}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', backgroundColor: 'var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
              <Mic size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Live Speech</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Real-time classroom translation</span>
            </div>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            Zero-jitter streaming audio & dual subtitles for teachers and students.
          </p>
        </div>

        <div
          className="white-card"
          style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
          onClick={() => setActiveTab('video')}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#7C3AED')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', backgroundColor: '#F3E8FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7C3AED' }}>
              <Video size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Video Translate</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Upload lecture videos</span>
            </div>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            Generate synchronized dual subtitles (SRT/WebVTT) and voice dubbing.
          </p>
        </div>

        <div
          className="white-card"
          style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
          onClick={() => setActiveTab('chat')}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#0D9488')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', backgroundColor: '#CCFBF1', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0D9488' }}>
              <MessageSquare size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>TRANSLARA AI</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Pedagogy assistant</span>
            </div>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            Multilingual concept explanations, simplified phrases, and lesson planning.
          </p>
        </div>

        <div
          className="white-card"
          style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
          onClick={() => setActiveTab('worksheets')}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#EA580C')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', backgroundColor: '#FFEDD5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#EA580C' }}>
              <FileText size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Worksheets</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Grades 1-3 PDFs</span>
            </div>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            Generate bilingual printable flashcards and literacy & numeracy worksheets.
          </p>
        </div>
      </div>
    </div>
  );
}
