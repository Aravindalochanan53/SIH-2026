import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Volume2, Sparkles, Trash2, Copy, Check } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { sendChatMessage, getChatHistory, clearChatHistory } from '../api';
import { LanguageSelector } from '../components/LanguageSelector';

export function ChatbotPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am TRANSLARA AI, your multilingual classroom pedagogy assistant. How can I help you today with lesson translations, vocabulary building, or primary school worksheets?',
      translated_text: 'வணக்கம்! நான் உங்கள் பன்மொழி கற்றல் உதவியாளர். உங்களுக்கு எப்படி உதவ முடியும்?',
      language: sourceLang,
      target_language: targetLang,
      timestamp: 'Just now',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);

  const suggestedPrompts = [
    'Translate a sentence',
    'Explain a concept',
    'Create a worksheet',
    'Simplify for Grade 1',
    'Create a classroom activity',
  ];

  useEffect(() => {
    getChatHistory()
      .then((history) => {
        if (history && history.length > 0) {
          setMessages(history);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textToSend = inputText) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg = {
      id: `u_${Date.now()}`,
      sender: 'user',
      text: textToSend.trim(),
      translated_text: '',
      language: sourceLang,
      target_language: targetLang,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const res = await sendChatMessage(userMsg.text, sourceLang, targetLang);
      const botMsg = {
        id: res.id || `b_${Date.now()}`,
        sender: 'assistant',
        text: res.text,
        translated_text: res.translated_text,
        language: res.language,
        target_language: res.target_language,
        timestamp: res.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `An error occurred: ${err.message}`,
          translated_text: '',
          language: sourceLang,
          target_language: targetLang,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await clearChatHistory();
    } catch (e) {}
    setMessages([]);
  };

  const handleCopyMessage = async (id, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {}
  };

  const handlePlayTTS = (text, lang) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const langMap = { en: 'en-US', ta: 'ta-IN', ml: 'ml-IN', te: 'te-IN', kn: 'kn-IN', hi: 'hi-IN' };
      utterance.lang = langMap[lang] || 'en-US';
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="page-container" style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Bar */}
      <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            TRANSLARA AI
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
            Your multilingual classroom assistant
          </p>
        </div>

        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />

        <button
          onClick={handleClear}
          className="icon-action-btn"
          title="Clear Conversation History"
        >
          <Trash2 size={14} />
          <span>Clear Chat</span>
        </button>
      </div>

      {/* Chat Messages Container */}
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0, marginTop: '12px' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((m) => {
            const isUser = m.sender === 'user';
            return (
              <div
                key={m.id}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  gap: '12px',
                  alignItems: 'flex-start',
                }}
              >
                {!isUser && (
                  <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid var(--primary-border)' }}>
                    <Bot size={18} />
                  </div>
                )}

                <div
                  style={{
                    maxWidth: '75%',
                    backgroundColor: isUser ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                    border: isUser ? 'none' : '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '14px 18px',
                    color: isUser ? '#ffffff' : 'var(--text-primary)',
                    boxShadow: 'var(--shadow-xs)',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>{m.text}</p>
                  
                  {m.translated_text && (
                    <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: isUser ? '1px solid rgba(255,255,255,0.2)' : '1px solid var(--border-color)', color: isUser ? 'rgba(255,255,255,0.9)' : 'var(--primary)', fontSize: '14px', fontWeight: 500 }}>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', display: 'block', marginBottom: '2px', opacity: 0.75, fontWeight: 700 }}>
                        Translation ({m.target_language?.toUpperCase() || targetLang.toUpperCase()})
                      </span>
                      {m.translated_text}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '11px', opacity: 0.7 }}>
                    <span>{m.timestamp}</span>
                    {!isUser && (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          onClick={() => handlePlayTTS(m.text, m.language)}
                          style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: '2px' }}
                          title="Listen"
                        >
                          <Volume2 size={13} />
                        </button>
                        <button
                          onClick={() => handleCopyMessage(m.id, m.text)}
                          style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: '2px' }}
                          title="Copy"
                        >
                          {copiedId === m.id ? <Check size={13} /> : <Copy size={13} />}
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {isUser && (
                  <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: 'var(--bg-surface-hover)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid var(--border-color)' }}>
                    <User size={18} />
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', color: 'var(--text-secondary)' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={18} />
              </div>
              <span style={{ fontSize: '13px' }}>AI is thinking & translating...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts Strip */}
        <div style={{ padding: '8px 16px', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-surface-secondary)', display: 'flex', gap: '8px', overflowX: 'auto' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', alignSelf: 'center', flexShrink: 0 }}>
            Suggested:
          </span>
          {suggestedPrompts.map((p, idx) => (
            <button
              key={`prompt-${idx}`}
              className="icon-action-btn"
              style={{ fontSize: '12px', padding: '4px 10px', whiteSpace: 'nowrap', backgroundColor: 'var(--bg-surface)' }}
              onClick={() => handleSend(p)}
            >
              <Sparkles size={12} color="var(--primary)" />
              <span>{p}</span>
            </button>
          ))}
        </div>

        {/* Message Input Box */}
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} style={{ display: 'flex', gap: '12px', padding: '16px', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-surface)' }}>
          <input
            type="text"
            placeholder="Type your question or request in English or any Indian language..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '10px 16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              backgroundColor: 'var(--bg-surface-secondary)',
              color: 'var(--text-primary)',
              fontSize: '14px',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !inputText.trim()}
            className="primary-action-btn"
          >
            <Send size={15} />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
