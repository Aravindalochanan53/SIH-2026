import React, { useState, useRef, useEffect } from 'react';
import { Mic, Volume2, Sparkles, Shield, Radio, Layers } from 'lucide-react';
import { LanguageSelector } from '../components/LanguageSelector';
import { AudioControls } from '../components/AudioControls';
import { LiveTranslator } from '../components/LiveTranslator';
import { LatencyIndicator } from '../components/LatencyIndicator';
import { WorksheetPanel } from '../components/WorksheetPanel';
import { useAppStore } from '../store/useAppStore';
import { StreamingAudioBridge } from '../websocket';

export function VoiceTranslatorPage() {
  const {
    sourceLang,
    targetLang,
    setSourceLang,
    setTargetLang,
    swapLanguages,
    voiceState,
    setVoiceState,
    addHistoryItem,
    isSimulatedOffline,
  } = useAppStore();

  const [isStreaming, setIsStreaming] = useState(false);
  const bridgeRef = useRef(null);

  useEffect(() => {
    return () => {
      if (bridgeRef.current) {
        bridgeRef.current.stop();
      }
    };
  }, []);

  const handleToggleStream = async () => {
    if (isStreaming) {
      if (bridgeRef.current) {
        bridgeRef.current.stop();
      }
      setIsStreaming(false);
      setVoiceState({ status: 'idle' });
    } else {
      setIsStreaming(true);
      setVoiceState({ status: 'connecting' });

      bridgeRef.current = new StreamingAudioBridge({
        onTranslation: (data) => {
          setVoiceState({
            status: 'speaking',
            transcript: data.original_text || data.transcript || data.source_text || '',
            translation: data.translation || data.translated_text || '',
            detectedLang: data.source_language || data.source_lang,
            entities: data.entities_locked || data.entities || [],
            latencyMs: data.latency_ms || 1450,
            stageLatencies: data.stage_latencies_ms || data.stages || {
              asr_ms: 580,
              entity_lock_ms: 22,
              nmt_ms: 680,
              unmask_ms: 12,
            },
            warning: data.warning || null,
            isOffline: data.offline || data.is_offline || false,
          });

          const origText = data.original_text || data.transcript || data.source_text;
          const trText = data.translation || data.translated_text;
          if (origText && trText) {
            addHistoryItem({
              id: `v_${Date.now()}`,
              type: 'voice',
              sourceLang: data.source_language || data.source_lang || sourceLang,
              targetLang: data.target_language || data.target_lang || targetLang,
              sourceText: origText,
              targetText: trText,
              date: 'Just now',
            });
          }
        },
        onStatusChange: (status) => {
          setVoiceState({ status });
        },
        onError: (err) => {
          console.error('Audio Stream Error:', err);
          setIsStreaming(false);
          setVoiceState({ status: 'error', warning: err?.message || 'Connection error' });
        },
      });

      try {
        await bridgeRef.current.start({ sourceLang, targetLang });
      } catch (e) {
        console.error('Failed to start bridge:', e);
        setIsStreaming(false);
        setVoiceState({ status: 'error', warning: e.message });
      }
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Live Speech Translation
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Real-time microphone speech recognition, entity-locked neural translation, and synthesized audio stream
        </p>
      </div>

      {/* Language Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="model-badge indic">
            <Radio size={12} />
            <span>16kHz PCM Stream</span>
          </span>
          <span className="model-badge">
            <Shield size={12} />
            <span>Entity Shield Active</span>
          </span>
        </div>
      </div>

      {/* Audio Controls */}
      <AudioControls
        isStreaming={isStreaming}
        onToggleStream={handleToggleStream}
        status={voiceState.status}
      />

      {/* Dual Live HUD Subtitles */}
      <LiveTranslator
        transcript={voiceState.transcript}
        translation={voiceState.translation}
        sourceLang={sourceLang}
        targetLang={targetLang}
        detectedLang={voiceState.detectedLang}
        entities={voiceState.entities}
        warning={voiceState.warning}
        isOffline={isSimulatedOffline || voiceState.isOffline}
      />

      {/* Latency Breakdown & Pedagogy Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        <LatencyIndicator
          latencyMs={voiceState.latencyMs}
          stages={voiceState.stageLatencies}
        />
        <WorksheetPanel sourceLang={sourceLang} targetLang={targetLang} />
      </div>
    </div>
  );
}
