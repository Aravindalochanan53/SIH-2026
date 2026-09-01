import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Sparkles, LogOut, User } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from './LanguageSelector';

export function Navbar() {
  const navigate = useNavigate();
  const {
    user,
    logout,
    sourceLang,
    targetLang,
    setSourceLang,
    setTargetLang,
    swapLanguages,
    capabilities,
  } = useAppStore();

  const isPairActive =
    capabilities?.languages?.[sourceLang]?.translation &&
    capabilities?.languages?.[targetLang]?.translation;

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <div className="search-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search lessons, phrases, worksheets..."
            className="search-input"
          />
        </div>
      </div>

      <div className="navbar-right">
        <div className="pair-status-badge">
          <span className={`status-dot ${isPairActive !== false ? 'green' : 'yellow'}`}></span>
          <span className="pair-text">
            {sourceLang.toUpperCase()} ⇄ {targetLang.toUpperCase()}
          </span>
        </div>

        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />

        <Link to="/video" className="demo-launch-btn" style={{ textDecoration: 'none' }}>
          <Sparkles size={15} />
          <span>Demo Video</span>
        </Link>

        {/* User Profile & Logout */}
        <Link to="/profile" className="navbar-user" style={{ textDecoration: 'none' }}>
          <div className="navbar-avatar">{initials}</div>
          <span className="navbar-user-name">{user?.name?.split(' ')[0] || 'User'}</span>
        </Link>

        <button
          onClick={handleLogout}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: 'var(--radius-sm)',
            transition: 'color 0.2s ease',
          }}
          title="Sign Out"
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--error-text)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
