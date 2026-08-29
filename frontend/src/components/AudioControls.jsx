import React from 'react';
import { Mic, MicOff, Activity, Radio } from 'lucide-react';

export function AudioControls({ isStreaming, onToggleStream, status }) {
  const bars = Array.from({ length: 20 });

  const getStatusDisplay = () => {
    switch (status) {
      case 'listening':
        return { label: 'Live Recording', color: 'var(--success)', dot: 'green' };
      case 'connecting':
        return { label: 'Connecting...', color: 'var(--warning)', dot: 'yellow' };
      case 'processing':
        return { label: 'Processing Audio', color: 'var(--primary)', dot: 'blue' };
      case 'speaking':
        return { label: 'Translating Speech', color: 'var(--primary)', dot: 'blue' };
      case 'error':
        return { label: 'Connection Error', color: 'var(--error)', dot: 'red' };
      default:
        return { label: 'Ready to Listen', color: 'var(--text-secondary)', dot: 'gray' };
    }
  };

  const statusInfo = getStatusDisplay();

  return (
    <div className="glass-panel controls-strip">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <button
          className={`mic-action-btn ${isStreaming ? 'stop' : 'start'}`}
          onClick={onToggleStream}
          aria-label={isStreaming ? 'Stop Recording' : 'Start Live Speech'}
        >
          {isStreaming ? <MicOff size={16} /> : <Mic size={16} />}
          <span>{isStreaming ? 'Stop Recording' : 'Start Live Speech'}</span>
        </button>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Microphone Status
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: statusInfo.color,
              }}
            />
            <span style={{ fontSize: '13px', fontWeight: 600, color: statusInfo.color }}>
              {statusInfo.label}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className="wave-bars">
          {bars.map((_, i) => (
            <div
              key={`bar-${i}`}
              className={`wave-bar ${isStreaming ? 'active' : ''}`}
              style={{
                animationDelay: `${(i % 6) * 0.1}s`,
                height: isStreaming ? `${12 + (i % 5) * 4}px` : '6px',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
