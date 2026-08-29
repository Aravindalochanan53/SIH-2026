import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

export function EntityPanel({ entities = [] }) {
  return (
    <div className="glass-panel" style={{ padding: '16px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={16} color="var(--primary)" />
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Entity Lock Inspector (Protected Proper Nouns & Numbers)
          </span>
        </div>
        <span className="model-badge">
          {entities.length} Protected
        </span>
      </div>

      {entities.length === 0 ? (
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          No locked entities detected in recent utterance. Numerical values and names will be deterministically preserved during translation.
        </p>
      ) : (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {entities.map((ent, idx) => (
            <span
              key={`ent-${idx}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 'var(--primary-light)',
                border: '1px solid var(--primary-border)',
                color: 'var(--primary)',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              <Lock size={11} />
              <span>{ent.text}</span>
              <span style={{ fontSize: '10px', opacity: 0.7 }}>({ent.type})</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
