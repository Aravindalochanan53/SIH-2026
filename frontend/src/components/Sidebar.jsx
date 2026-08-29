import React from 'react';
import {
  Mic,
  Video,
  MessageSquare,
  Radio,
  BookOpen,
  FileText,
  WifiOff,
  History,
  Settings,
  Languages,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export function Sidebar() {
  const { activeTab, setActiveTab } = useAppStore();

  const navItems = [
    { id: 'home', label: 'Translator', icon: Languages },
    { id: 'voice', label: 'Live Speech', icon: Mic, badge: 'Live' },
    { id: 'video', label: 'Video', icon: Video, badge: 'HD' },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare, badge: 'AI' },
    { id: 'meeting', label: 'Live Meeting', icon: Radio },
    { id: 'learning', label: 'Flashcards', icon: BookOpen },
    { id: 'worksheets', label: 'Worksheets', icon: FileText },
    { id: 'offline', label: 'Offline Library', icon: WifiOff },
    { id: 'history', label: 'History', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar-nav">
      <div className="sidebar-brand" onClick={() => setActiveTab('home')}>
        <div className="brand-logo-icon">TL</div>
        <div className="brand-text">
          <span className="brand-name">TRANSLARA</span>
          <span className="brand-badge">EdTech AI</span>
        </div>
      </div>

      <nav className="nav-menu" aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {item.badge && (
                <span className={`nav-pill ${item.badge === 'Live' ? 'new' : ''}`}>
                  {item.badge}
                </span>
              )}
            </button>
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
