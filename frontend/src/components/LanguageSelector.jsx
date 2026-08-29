import React, { useEffect, useState } from 'react';
import { ArrowLeftRight, Globe2, ChevronDown, Search } from 'lucide-react';
import { getLanguages } from '../api';

export const DEFAULT_LANGUAGES = [
  { code: 'en', name: 'English', native_name: 'English', region: 'English' },
  { code: 'ta', name: 'Tamil', native_name: 'தமிழ்', region: 'South India' },
  { code: 'te', name: 'Telugu', native_name: 'తెలుగు', region: 'South India' },
  { code: 'kn', name: 'Kannada', native_name: 'ಕನ್ನಡ', region: 'South India' },
  { code: 'ml', name: 'Malayalam', native_name: 'മലയാളം', region: 'South India' },
  { code: 'hi', name: 'Hindi', native_name: 'हिन्दी', region: 'North / Other India' },
  { code: 'sat', name: 'Santhali', native_name: 'ᱥᱟᱱᱛᱟᱲᱤ', region: 'North / Other India' },
  { code: 'hoc', name: 'Ho', native_name: 'Ho (हो)', region: 'North / Other India' },
  { code: 'unr', name: 'Mundari', native_name: 'Mundari (मुंडारी)', region: 'North / Other India' },
];

export function LanguageSelector({
  sourceLang,
  targetLang,
  onSourceChange,
  onTargetChange,
  onSwap,
}) {
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES);

  useEffect(() => {
    getLanguages()
      .then((data) => {
        if (data.languages && data.languages.length > 0) {
          setLanguages(data.languages);
        }
      })
      .catch(() => {
        // Default list is already set
      });
  }, []);

  const getLangName = (code) => {
    const l = languages.find((item) => item.code === code);
    return l ? `${l.name} — ${l.native_name}` : code.toUpperCase();
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
      {/* Source Language Picker */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Source Language
        </span>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <select
            value={sourceLang}
            onChange={(e) => onSourceChange(e.target.value)}
            aria-label="Source Language"
            style={{
              appearance: 'none',
              backgroundColor: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 36px 8px 14px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              cursor: 'pointer',
              outline: 'none',
              minWidth: '180px',
            }}
          >
            {languages.map((l) => (
              <option key={`src-${l.code}`} value={l.code} disabled={l.code === targetLang}>
                {l.name} — {l.native_name}
              </option>
            ))}
          </select>
          <ChevronDown size={15} style={{ position: 'absolute', right: '12px', pointerEvents: 'none', color: 'var(--text-secondary)' }} />
        </div>
      </div>

      {/* Swap Button */}
      <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', paddingTop: '18px' }}>
        <button
          onClick={onSwap}
          title="Swap Languages"
          aria-label="Swap Languages"
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-xs)',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--primary-light)';
            e.currentTarget.style.borderColor = 'var(--primary)';
            e.currentTarget.style.color = 'var(--primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--bg-surface)';
            e.currentTarget.style.borderColor = 'var(--border-color)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }}
        >
          <ArrowLeftRight size={15} />
        </button>
      </div>

      {/* Target Language Picker */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Target Language
        </span>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <select
            value={targetLang}
            onChange={(e) => onTargetChange(e.target.value)}
            aria-label="Target Language"
            style={{
              appearance: 'none',
              backgroundColor: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 36px 8px 14px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              cursor: 'pointer',
              outline: 'none',
              minWidth: '180px',
            }}
          >
            {languages.map((l) => (
              <option key={`tgt-${l.code}`} value={l.code} disabled={l.code === sourceLang}>
                {l.name} — {l.native_name}
              </option>
            ))}
          </select>
          <ChevronDown size={15} style={{ position: 'absolute', right: '12px', pointerEvents: 'none', color: 'var(--text-secondary)' }} />
        </div>
      </div>
    </div>
  );
}
