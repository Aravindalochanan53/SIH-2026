import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Languages,
  Mic,
  Video,
  MessageSquare,
  Radio,
  BookOpen,
  FileText,
  WifiOff,
  History,
  Settings,
} from 'lucide-react';

export function Sidebar() {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/translate', label: 'Translator', icon: Languages },
    { to: '/voice', label: 'Live Speech', icon: Mic, badge: 'Live' },
    { to: '/video', label: 'Video', icon: Video, badge: 'HD' },
    { to: '/chat', label: 'AI Chat', icon: MessageSquare, badge: 'AI' },
    { to: '/meeting', label: 'Live Meeting', icon: Radio },
    { to: '/learning', label: 'Flashcards', icon: BookOpen },
    { to: '/worksheets', label: 'Worksheets', icon: FileText },
    { to: '/offline', label: 'Offline Library', icon: WifiOff },
    { to: '/history', label: 'History', icon: History },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar-nav">
      <Link to="/" className="sidebar-brand">
        <div className="brand-logo-icon">TL</div>
        <div className="brand-text">
          <span className="brand-name">TRANSLARA</span>
          <span className="brand-badge">EdTech AI</span>
        </div>
      </Link>

      <nav className="nav-menu" aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {item.badge && (
                <span className={`nav-pill ${item.badge === 'Live' ? 'new' : ''}`}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator-pill">
          <span className="pulse-dot"></span>
          <span>Pan-Indian AI Active</span>
        </div>
      </div>
    </aside>
  );
}
