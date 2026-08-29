import React, { useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { HomePage } from './pages/HomePage';
import { VoiceTranslatorPage } from './pages/VoiceTranslatorPage';
import { VideoTranslatorPage } from './pages/VideoTranslatorPage';
import { ChatbotPage } from './pages/ChatbotPage';
import { LiveMeetingPage } from './pages/LiveMeetingPage';
import { LearningPage } from './pages/LearningPage';
import { WorksheetsPage } from './pages/WorksheetsPage';
import { OfflinePage } from './pages/OfflinePage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { useAppStore } from './store/useAppStore';
import { getCapabilities } from './api';

export default function App() {
  const { activeTab, setCapabilities } = useAppStore();

  useEffect(() => {
    getCapabilities()
      .then(setCapabilities)
      .catch((e) => console.log('Capabilities load notice:', e));
  }, [setCapabilities]);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage />;
      case 'voice':
        return <VoiceTranslatorPage />;
      case 'video':
        return <VideoTranslatorPage />;
      case 'chat':
        return <ChatbotPage />;
      case 'meeting':
        return <LiveMeetingPage />;
      case 'learning':
        return <LearningPage />;
      case 'worksheets':
        return <WorksheetsPage />;
      case 'offline':
        return <OfflinePage />;
      case 'history':
        return <HistoryPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <HomePage />;
    }
  };

  return (
    <div className="app-layout-shell">
      <Sidebar />
      <div className="main-content-wrapper">
        <Navbar />
        <main className="page-content-area">{renderActivePage()}</main>
      </div>
    </div>
  );
}
