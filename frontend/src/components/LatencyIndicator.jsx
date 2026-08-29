import React, { useState } from 'react';
import { Clock, ChevronDown, ChevronUp, Cpu, Shield, ArrowRight } from 'lucide-react';

export function LatencyIndicator({ latencyMs = 1450, stages = {} }) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const getLatencyStatus = (ms) => {
    if (ms <= 2000) return { label: 'Optimal (< 2.0s)', color: 'var(--success)' };
    if (ms <= 3000) return { label: 'Good (< 3.0s)', color: 'var(--warning)' };
    return { label: 'High Latency', color: 'var(--error)' };
  };

  const status = getLatencyStatus(latencyMs);

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={16} color="var(--primary)" />
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Pipeline Latency
          </span>
        </div>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: `${status.color}15`,
            color: status.color,
          }}
        >
          {status.label}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '14px' }}>
        <span style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)' }}>
          {(latencyMs / 1000).toFixed(2)}
        </span>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>seconds</span>
      </div>

      {/* Expandable Technical Details Button */}
      <button
        onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'none',
          border: 'none',
          color: 'var(--primary)',
          fontSize: '12px',
          fontWeight: 600,
          cursor: 'pointer',
          padding: 0,
        }}
      >
        <span>{showTechnicalDetails ? 'Hide Technical Details' : 'View Technical Details'}</span>
        {showTechnicalDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {showTechnicalDetails && (
        <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>ASR (Faster-Whisper INT8)</span>
              <span style={{ fontWeight: 600 }}>{stages.asr_ms || 580} ms</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${Math.min(100, ((stages.asr_ms || 580) / 1200) * 100)}%`, height: '100%', backgroundColor: 'var(--primary)' }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Entity Lock Shield</span>
              <span style={{ fontWeight: 600 }}>{stages.entity_lock_ms || 22} ms</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${Math.min(100, ((stages.entity_lock_ms || 22) / 100) * 100)}%`, height: '100%', backgroundColor: '#8B5CF6' }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>NMT (IndicTrans2)</span>
              <span style={{ fontWeight: 600 }}>{stages.nmt_ms || 680} ms</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${Math.min(100, ((stages.nmt_ms || 680) / 1400) * 100)}%`, height: '100%', backgroundColor: '#0D9488' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
