import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Shield, Languages, LogOut, Clock, Activity } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout, savedTranslations } = useAppStore();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  if (!user) {
    return (
      <div className="page-container animate-fade-in">
        <div className="glass-panel" style={{ textAlign: 'center', padding: '48px' }}>
          <p style={{ color: 'var(--text-secondary)' }}>Please log in to view your profile.</p>
        </div>
      </div>
    );
  }

  const initials = user.name
    ? user.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const voiceCount = savedTranslations.filter((t) => t.type === 'voice').length;
  const textCount = savedTranslations.filter((t) => t.type === 'text' || t.type === 'saved').length;
  const videoCount = savedTranslations.filter((t) => t.type === 'video').length;

  return (
    <div className="page-container animate-fade-in">
      {/* Profile Header Card */}
      <div className="glass-panel">
        <div className="profile-card">
          <div className="profile-avatar-large">{initials}</div>
          <div className="profile-info">
            <h2>{user.name}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>{user.email}</p>
            <span className={`role-badge ${user.role}`}>
              {user.role === 'admin' ? '🛡️ Administrator' : '👩‍🏫 Teacher'}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {/* Preferences */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', paddingBottom: '14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <Languages size={16} color="var(--primary)" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Language Preferences</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Source Language</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', padding: '4px 12px', background: 'var(--primary-light)', borderRadius: 'var(--radius-full)', border: '1px solid var(--primary-border)' }}>
                {(user.preferred_source_lang || 'ta').toUpperCase()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Target Language</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', padding: '4px 12px', background: 'rgba(139, 92, 246, 0.12)', borderRadius: 'var(--radius-full)', border: '1px solid rgba(139, 92, 246, 0.25)' }}>
                {(user.preferred_target_lang || 'ml').toUpperCase()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Account Status</span>
              <span style={{ fontSize: '12px', fontWeight: 600, color: user.is_active ? 'var(--success-text)' : 'var(--error-text)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: user.is_active ? 'var(--success)' : 'var(--error)' }} />
                {user.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        {/* Translation Stats */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', paddingBottom: '14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <Activity size={16} color="var(--accent-teal)" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Translation Summary</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
            {[
              { label: 'Text', count: textCount, color: 'var(--primary)' },
              { label: 'Voice', count: voiceCount, color: 'var(--success)' },
              { label: 'Video', count: videoCount, color: 'var(--accent-purple)' },
            ].map((s) => (
              <div key={s.label} style={{
                textAlign: 'center', padding: '16px 10px',
                background: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}>
                <div style={{ fontSize: '24px', fontWeight: 800, color: s.color }}>{s.count}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Logout */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={handleLogout} className="ghost-btn" style={{ color: 'var(--error-text)' }}>
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
