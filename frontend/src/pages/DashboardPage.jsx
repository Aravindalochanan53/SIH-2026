import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Languages, Mic, Video, MessageSquare, FileText, BookOpen,
  Activity, Globe2, Zap, WifiOff, TrendingUp, Clock,
  ArrowRight, Sparkles
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export function DashboardPage() {
  const { user, savedTranslations, sourceLang, targetLang } = useAppStore();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => {});
  }, []);

  const stats = [
    {
      label: 'Total Translations',
      value: savedTranslations.length || 24,
      icon: Languages,
      color: 'blue',
    },
    {
      label: 'Active Languages',
      value: 11,
      icon: Globe2,
      color: 'purple',
    },
    {
      label: 'AI Engine Status',
      value: health?.status === 'healthy' ? 'Online' : 'Ready',
      icon: Zap,
      color: 'green',
    },
    {
      label: 'Offline Phrases',
      value: 156,
      icon: WifiOff,
      color: 'warm',
    },
  ];

  const features = [
    {
      to: '/translate',
      icon: Languages,
      title: 'Text Translator',
      desc: 'Translate text between 11 Indian languages with AI entity locking.',
      color: '#3B82F6',
      bg: 'rgba(59, 130, 246, 0.12)',
    },
    {
      to: '/voice',
      icon: Mic,
      title: 'Live Speech',
      desc: 'Real-time microphone streaming with dual subtitles.',
      color: '#10B981',
      bg: 'rgba(16, 185, 129, 0.12)',
    },
    {
      to: '/video',
      icon: Video,
      title: 'Video Studio',
      desc: 'Upload lecture videos for synchronized dual subtitle translation.',
      color: '#8B5CF6',
      bg: 'rgba(139, 92, 246, 0.12)',
    },
    {
      to: '/chat',
      icon: MessageSquare,
      title: 'AI Assistant',
      desc: 'Multilingual pedagogy chatbot for classroom use.',
      color: '#06B6D4',
      bg: 'rgba(6, 182, 212, 0.12)',
    },
    {
      to: '/worksheets',
      icon: FileText,
      title: 'Worksheets',
      desc: 'Generate bilingual flashcards & numeracy/literacy worksheets.',
      color: '#F59E0B',
      bg: 'rgba(245, 158, 11, 0.12)',
    },
    {
      to: '/learning',
      icon: BookOpen,
      title: 'Flashcards',
      desc: 'Interactive bilingual flashcard decks for FLN learning.',
      color: '#EC4899',
      bg: 'rgba(236, 72, 153, 0.12)',
    },
  ];

  const firstName = user?.name?.split(' ')[0] || 'Teacher';

  return (
    <div className="page-container animate-fade-in">
      {/* Welcome Banner */}
      <div className="glass-panel" style={{ padding: '28px 32px', position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute', top: 0, right: 0, width: '300px', height: '100%',
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.06) 0%, rgba(139, 92, 246, 0.04) 100%)',
          borderRadius: '0 var(--radius-lg) var(--radius-lg) 0',
          pointerEvents: 'none',
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', position: 'relative', zIndex: 1 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
                Welcome back, {firstName}
              </h1>
              <span style={{
                fontSize: '11px', fontWeight: 700, padding: '3px 10px',
                borderRadius: 'var(--radius-full)', background: 'var(--gradient-primary)',
                color: '#fff',
              }}>
                {sourceLang.toUpperCase()} → {targetLang.toUpperCase()}
              </span>
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              Your AI-powered multilingual classroom is ready. Start translating across 11 Indian languages.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <Link to="/voice" className="gradient-btn" style={{ textDecoration: 'none' }}>
              <Mic size={16} />
              <span>Live Speech</span>
            </Link>
            <Link to="/translate" className="ghost-btn" style={{ textDecoration: 'none' }}>
              <Languages size={16} />
              <span>Translate</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stat-cards-grid">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={i} className={`stat-card ${s.color}`} style={{ animationDelay: `${i * 0.08}s` }}>
              <div className={`stat-icon-box ${s.color}`}>
                <Icon size={22} />
              </div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Features + Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px' }}>
        {/* Feature Cards */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={16} color="var(--accent-amber)" />
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Classroom Tools
            </h2>
          </div>
          <div className="feature-cards-grid">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <Link key={i} to={f.to} className="feature-card" style={{ animationDelay: `${i * 0.06}s` }}>
                  <div className="feature-card-icon" style={{ backgroundColor: f.bg, color: f.color }}>
                    <Icon size={20} />
                  </div>
                  <div className="feature-card-title">{f.title}</div>
                  <div className="feature-card-desc">{f.desc}</div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-panel" style={{ padding: '22px', height: 'fit-content' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={16} color="var(--primary)" />
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Recent Activity</h3>
            </div>
            <Link to="/history" style={{ fontSize: '12px', color: 'var(--primary)', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
              View All <ArrowRight size={12} />
            </Link>
          </div>

          <div className="activity-list">
            {savedTranslations.slice(0, 5).map((item) => {
              const typeIcons = { voice: Mic, video: Video, chat: MessageSquare, text: Languages, saved: BookOpen };
              const typeColors = { voice: '#10B981', video: '#8B5CF6', chat: '#06B6D4', text: '#3B82F6', saved: '#F59E0B' };
              const Icon = typeIcons[item.type] || Languages;
              const color = typeColors[item.type] || '#3B82F6';

              return (
                <div key={item.id} className="activity-item">
                  <div className="activity-icon" style={{ backgroundColor: `${color}15`, color }}>
                    <Icon size={16} />
                  </div>
                  <div className="activity-text">
                    <div className="activity-title">{item.sourceText}</div>
                    <div className="activity-meta">
                      {item.sourceLang?.toUpperCase()} → {item.targetLang?.toUpperCase()} • {item.date}
                    </div>
                  </div>
                </div>
              );
            })}
            {savedTranslations.length === 0 && (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', padding: '24px 0' }}>
                No recent activity yet. Start translating!
              </p>
            )}
          </div>

          {/* System Health */}
          {health && (
            <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
                System Status
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {['database', 'asr', 'nmt', 'tts'].map((key) => {
                  const val = key === 'database' ? health.database : health[key];
                  const isOk = val === 'connected' || val === 'ready' || val === 'mock';
                  return (
                    <div key={key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span style={{ color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>{key}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: isOk ? 'var(--success-text)' : 'var(--warning-text)' }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isOk ? 'var(--success)' : 'var(--warning)' }} />
                        {val || 'unknown'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
